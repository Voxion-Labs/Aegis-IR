#include <algorithm>
#include <cmath>
#include <cctype>
#include <cstring>
#include <iomanip>
#include <sstream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#define AEGIS_EXPORT EMSCRIPTEN_KEEPALIVE
#else
#define AEGIS_EXPORT
#endif

namespace {

struct AegisDocument {
    int id;
    const char* title;
    const char* category;
    const char* body;
};

struct AegisHit {
    int document_index;
    double score;
    std::vector<std::string> matched_terms;
};

std::vector<std::string> tokenize(const std::string& text) {
    std::vector<std::string> tokens;
    std::string current;
    current.reserve(32);

    for (unsigned char ch : text) {
        if (std::isalnum(ch)) {
            current.push_back(static_cast<char>(std::tolower(ch)));
            continue;
        }

        if (!current.empty()) {
            tokens.push_back(current);
            current.clear();
        }
    }

    if (!current.empty()) {
        tokens.push_back(current);
    }

    return tokens;
}

std::string escape_json(const std::string& value) {
    std::ostringstream out;

    for (char ch : value) {
        switch (ch) {
            case '\\':
                out << "\\\\";
                break;
            case '"':
                out << "\\\"";
                break;
            case '\n':
                out << "\\n";
                break;
            case '\r':
                out << "\\r";
                break;
            case '\t':
                out << "\\t";
                break;
            default:
                out << ch;
                break;
        }
    }

    return out.str();
}

class AegisEngine {
public:
    AegisEngine()
        : documents_{
              {1, "Deterministic Memory for Browser Search", "Memory Systems",
               "Aegis-IR compiles a C++ information retrieval kernel to WebAssembly so "
               "query scoring executes inside linear memory rather than allocating many "
               "short lived JavaScript objects."},
              {2, "V8 Garbage Collection Pressure in Client Retrieval", "Runtime Analysis",
               "Vanilla JavaScript search implementations often allocate token arrays, "
               "temporary maps, result objects, and intermediate strings during each query. "
               "Those allocations increase V8 heap pressure and can trigger visible "
               "garbage collection pauses."},
              {3, "Flat TF-IDF Matrices in WebAssembly", "Information Retrieval",
               "A continuous term frequency matrix provides deterministic memory traversal "
               "for TF-IDF scoring. Query terms index directly into contiguous numeric "
               "buffers owned by the Wasm module."},
              {4, "Main-Thread Stutter Telemetry", "Browser Instrumentation",
               "Aegis-IR measures blocking time as the user types, separating deterministic "
               "ranking execution from rendering work and garbage-collector induced stalls."},
              {5, "Voxion Labs Aegis-IR Architecture", "Applied Research",
               "Aegis-IR is a zero-backend browser-native information retrieval project "
               "focused on deterministic memory isolation, WebAssembly linear memory, and "
               "garbage collection avoidance."},
          } {
        build_index();
    }

    std::string search_as_json(const char* raw_query) const {
        const std::string query = raw_query == nullptr ? "" : raw_query;
        const std::vector<std::string> query_terms = unique_terms(tokenize(query));

        if (query_terms.empty()) {
            return "{\"query\":\"" + escape_json(query) + "\",\"count\":0,\"results\":[]}";
        }

        std::vector<AegisHit> hits;
        hits.reserve(documents_.size());

        for (std::size_t doc_index = 0; doc_index < documents_.size(); ++doc_index) {
            double score = 0.0;
            std::vector<std::string> matched_terms;

            for (const std::string& term : query_terms) {
                const auto term_it = vocabulary_.find(term);
                if (term_it == vocabulary_.end()) {
                    continue;
                }

                const std::size_t term_index = term_it->second;
                const int frequency = term_frequencies_[matrix_offset(doc_index, term_index)];
                if (frequency == 0) {
                    continue;
                }

                // Critical memory-management property:
                // the hot TF-IDF loop only reads from contiguous numeric arrays already
                // allocated inside WebAssembly linear memory. It does not construct JS
                // strings, JS arrays, JS Maps, or per-document JS result objects while
                // scoring. This keeps V8 heap pressure flat and avoids GC-triggered
                // main-thread pauses during ranking.
                const double tf = 1.0 + std::log(static_cast<double>(frequency));
                const double idf = inverse_document_frequency_[term_index];
                score += tf * idf;
                matched_terms.push_back(term);
            }

            if (score > 0.0) {
                hits.push_back(AegisHit{static_cast<int>(doc_index), score, matched_terms});
            }
        }

        std::sort(hits.begin(), hits.end(), [](const AegisHit& left, const AegisHit& right) {
            if (std::fabs(left.score - right.score) > 0.000001) {
                return left.score > right.score;
            }

            return left.document_index < right.document_index;
        });

        return serialize_results(query, hits);
    }

    int document_count() const {
        return static_cast<int>(documents_.size());
    }

    int linear_memory_bytes() const {
        return static_cast<int>((term_frequencies_.size() * sizeof(int)) +
                                (inverse_document_frequency_.size() * sizeof(double)));
    }

private:
    std::vector<AegisDocument> documents_;
    std::unordered_map<std::string, std::size_t> vocabulary_;
    std::vector<int> term_frequencies_;
    std::vector<int> document_frequencies_;
    std::vector<double> inverse_document_frequency_;

    void build_index() {
        std::vector<std::vector<std::string>> tokenized_documents;
        tokenized_documents.reserve(documents_.size());

        for (const AegisDocument& document : documents_) {
            std::vector<std::string> tokens = tokenize(std::string(document.title) + " " +
                                                       document.category + " " +
                                                       document.body);

            for (const std::string& token : tokens) {
                if (vocabulary_.find(token) == vocabulary_.end()) {
                    vocabulary_[token] = vocabulary_.size();
                }
            }

            tokenized_documents.push_back(tokens);
        }

        const std::size_t term_count = vocabulary_.size();
        term_frequencies_.assign(documents_.size() * term_count, 0);
        document_frequencies_.assign(term_count, 0);
        inverse_document_frequency_.assign(term_count, 0.0);

        for (std::size_t doc_index = 0; doc_index < tokenized_documents.size(); ++doc_index) {
            std::unordered_set<std::size_t> seen_terms;

            for (const std::string& token : tokenized_documents[doc_index]) {
                const std::size_t term_index = vocabulary_[token];
                ++term_frequencies_[matrix_offset(doc_index, term_index)];
                seen_terms.insert(term_index);
            }

            for (std::size_t term_index : seen_terms) {
                ++document_frequencies_[term_index];
            }
        }

        for (std::size_t term_index = 0; term_index < term_count; ++term_index) {
            inverse_document_frequency_[term_index] =
                std::log((1.0 + static_cast<double>(documents_.size())) /
                         (1.0 + static_cast<double>(document_frequencies_[term_index]))) +
                1.0;
        }
    }

    std::size_t matrix_offset(std::size_t document_index, std::size_t term_index) const {
        return document_index * vocabulary_.size() + term_index;
    }

    static std::vector<std::string> unique_terms(const std::vector<std::string>& terms) {
        std::vector<std::string> unique;
        std::unordered_set<std::string> seen;

        for (const std::string& term : terms) {
            if (seen.insert(term).second) {
                unique.push_back(term);
            }
        }

        return unique;
    }

    std::string serialize_results(const std::string& query, const std::vector<AegisHit>& hits) const {
        std::ostringstream json;
        json << std::fixed << std::setprecision(6);
        json << "{\"query\":\"" << escape_json(query)
             << "\",\"count\":" << hits.size()
             << ",\"linearMemoryBytes\":" << linear_memory_bytes()
             << ",\"results\":[";

        for (std::size_t i = 0; i < hits.size(); ++i) {
            const AegisHit& hit = hits[i];
            const AegisDocument& document = documents_[hit.document_index];

            if (i > 0) {
                json << ",";
            }

            json << "{\"id\":" << document.id
                 << ",\"title\":\"" << escape_json(document.title)
                 << "\",\"category\":\"" << escape_json(document.category)
                 << "\",\"excerpt\":\"" << escape_json(document.body)
                 << "\",\"score\":" << hit.score
                 << ",\"matchedTerms\":[";

            for (std::size_t term_index = 0; term_index < hit.matched_terms.size(); ++term_index) {
                if (term_index > 0) {
                    json << ",";
                }

                json << "\"" << escape_json(hit.matched_terms[term_index]) << "\"";
            }

            json << "]}";
        }

        json << "]}";
        return json.str();
    }
};

AegisEngine& engine() {
    static AegisEngine instance;
    return instance;
}

char* copy_to_linear_memory_result(const std::string& value) {
    char* buffer = new char[value.size() + 1];
    std::memcpy(buffer, value.c_str(), value.size() + 1);
    return buffer;
}

}  // namespace

extern "C" {

AEGIS_EXPORT char* aegis_search(const char* query) {
    return copy_to_linear_memory_result(engine().search_as_json(query));
}

AEGIS_EXPORT int aegis_document_count() {
    return engine().document_count();
}

AEGIS_EXPORT int aegis_linear_memory_bytes() {
    return engine().linear_memory_bytes();
}

AEGIS_EXPORT void aegis_free_result(char* result) {
    delete[] result;
}

}
