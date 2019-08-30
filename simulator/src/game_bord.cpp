#include <boost/property_tree/json_parser.hpp>
#include <boost/foreach.hpp>
namespace beast = boost::beast;
namespace http = beast::http;
namespace net = boost::asio;
using tcp = boost::asio::ip::tcp;
namespace pt = boost::property_tree;

struct Tile {
    int score, have_team;
    bool on_agent;
};

struct Agent {
    int agent_id, x, y;
};

struct Actions {
    int agent_id, dx, dy, apply, turn;
    std::string type;
};


class GameBord {
private:
    std::vector<std::vector<Tile>> game_field_;
    int width_, height_;
    int teamID_[2];
    int turn_ = 0;
    std::vector<Agent> agent_coordinate_[2];

public:
    void initalize_fields() {
        std::cout << "Input filed json file." << std::endl;
        std::string filename;
        std::cin >> filename;
        pt::ptree filed_json;
        read_json(filename, filed_json);
        width_ = filed_json.get_optional<int>("width").get();
        height_ = filed_json.get_optional<int>("height").get();
        std::cout << "width: " << width_ << std::endl;
        std::cout << "height: " << height_ << std::endl;

        // Set field score.
        for (auto first_nest : filed_json.get_child("points")) {
            std::vector<Tile> horizontal_vector;
            for (auto second_nest : first_nest.second) {
                int score = second_nest.second.get_optional<int>("").get();
                horizontal_vector.push_back({
                    score, 0, false
                });
            }
            game_field_.push_back(horizontal_vector);
        }

        // Set tiles
        std::pair<int, int> coordinate = {0, 0}; // x, y
        for (auto first_nest : filed_json.get_child("tiled")) {
            for (auto second_nest : first_nest.second) {
                int team = second_nest.second.get_optional<int>("").get();
                game_field_[coordinate.first][coordinate.second].have_team = team;
                ++coordinate.second;
            }
            ++coordinate.first;
            coordinate.second = 0;
        }

        // Set agents
        for (auto teams : filed_json.get_child("teams")) {
            int id = teams.second.get_optional<int>("teamID").get();
            teamID_[id % 2] = id;
            for (auto agent : teams.second.get_child("agents")) {
                auto data  = agent.second;
                agent_coordinate_[id % 2].push_back({
                    data.get_optional<int>("agentID").get(),
                    data.get_optional<int>("x").get(),
                    data.get_optional<int>("y").get()
                });
            }
        }
    }
};