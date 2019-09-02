#include <boost/property_tree/json_parser.hpp>
#include <boost/foreach.hpp>
#include <time.h>
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
    bool init_check_ = false;
    int width_, height_;
    int teamID_[2];
    int turn_ = 0;
    std::vector<Agent> agent_coordinate_[2];
    std::vector<std::vector<bool>> area_count_;
    // information
    int matchID_ = 1;
    int interval_millisecond_ = 10 * 1000;
    std::string match_name_ = "temporary";
    int turn_millisecond_ = 1 * 1000;
    int max_turns_ = 100;
    
    int unix_time_;
    

    void tile_not_surrounded(int team_id, int x, int y) {
        if (game_field_[x][y].have_team == team_id || area_count_[x][y]) return;
        area_count_[x][y] = true;
        if (x > 0) tile_not_surrounded(team_id, x - 1, y);
        if (y > 0) tile_not_surrounded(team_id, x, y - 1);
        if (x < height_ - 1) tile_not_surrounded(team_id, x + 1, y);
        if (y < width_ - 1) tile_not_surrounded(team_id, x, y + 1);
    }

public:
    void initalize_fields() {
        if (init_check_) {
            std::cout << "Already init" << std::endl;
            return;
        }
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

        // confirm
        for (int i = 0; i < 2; i++) {
            tile_point_caluculate(teamID_[i]);
            area_point_calculate(teamID_[i]);
        }

        unix_time_ = time(nullptr);
        std::cout << "unix time: " << unix_time_ << std::endl;
    }

    int tile_point_caluculate(int team_id) {
        int tile_point = 0;
        for (int i = 0; i < height_; i++) {
            for (int j = 0; j < width_; j++) {
                if (game_field_[i][j].have_team == team_id) tile_point += game_field_[i][j].score;
            }
        }
        std::cout << team_id << " have tile point: " << tile_point << std::endl;
        return tile_point;
    }

    int area_point_calculate(int team_id) {
        if (area_count_.empty()) {
            // init
            for (int i = 0; i < height_; i++) {
                std::vector<bool> horizonal_vector(width_, false);
                area_count_.push_back(horizonal_vector);
            }
        } else {
            for (int i = 0; i < height_; i++) {
                for (int j = 0; j < width_; j++) {
                    area_count_[i][j] = false;
                }
            }
        }

        for (int i = 0; i < height_; i++) {
            tile_not_surrounded(team_id, i, 0);
            tile_not_surrounded(team_id, i, width_ - 1);
        }

        for (int i = 0; i < width_; i++) {
            tile_not_surrounded(team_id, 0, i);
            tile_not_surrounded(team_id, height_ - 1, i);
        }

        int area_point = 0;
        for (int i = 0; i < height_; i++) {
            for (int j = 0; j < width_; j++) {
                if (game_field_[i][j].have_team != team_id && !area_count_[i][j]) {
                    area_point += abs(game_field_[i][j].score);
                }
            }
        }
        std::cout << team_id << " have area point: " << area_point << std::endl;
        return area_point;
    }
};