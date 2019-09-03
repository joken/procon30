#include <boost/property_tree/json_parser.hpp>
#include <boost/foreach.hpp>
#include <time.h>
#include "picojson.h"
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
    int interval_millisecond_;
    std::string match_name_ = "temporary";
    int turn_millisecond_;
    int max_turn_;
    int started_unix_time_;
    // game history
    std::vector<Actions> agent_actions_[2];
    std::vector<Actions> actions_history_;
    

    void tile_not_surrounded(int team_id, int x, int y) {
        if (game_field_[x][y].have_team == team_id || area_count_[x][y]) return;
        area_count_[x][y] = true;
        if (x > 0) tile_not_surrounded(team_id, x - 1, y);
        if (y > 0) tile_not_surrounded(team_id, x, y - 1);
        if (x < height_ - 1) tile_not_surrounded(team_id, x + 1, y);
        if (y < width_ - 1) tile_not_surrounded(team_id, x, y + 1);
    }

    int tile_point_calculate(int team_id) {
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

public:
    int get_started_unix_time() {return started_unix_time_;}
    int get_interval_millisecond() {return interval_millisecond_;}
    int get_turn_millisecond() {return turn_millisecond_;};
    // I use boost::property_tree instead of picojson to read json files. I will rewrite picojson if I'm free.
    void initialize_fields(int interval_millisecond, int turn_millisecond, int max_turn, int between) {
        interval_millisecond_ = interval_millisecond;
        turn_millisecond_ = turn_millisecond;
        max_turn_ = max_turn;
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
        for (const auto& first_nest : filed_json.get_child("points")) {
            std::vector<Tile> horizontal_vector;
            for (const auto& second_nest : first_nest.second) {
                int score = second_nest.second.get_optional<int>("").get();
                horizontal_vector.push_back({
                    score, 0, false
                });
            }
            game_field_.push_back(horizontal_vector);
        }

        // Set tiles
        std::pair<int, int> coordinate = {0, 0}; // x, y
        for (const auto& first_nest : filed_json.get_child("tiled")) {
            for (const auto& second_nest : first_nest.second) {
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
                agent_actions_[id % 2].push_back({
                    data.get_optional<int>("agentID").get(),
                    0,
                    0,
                    1,
                    turn_,
                    "stay"
                });
            }
        }

        // confirm
        for (int i : teamID_) {
            tile_point_calculate(i);
            area_point_calculate(i);
        }

        started_unix_time_ = time(nullptr) + between;
        std::cout << "unix time: " << started_unix_time_ << std::endl;
    }

    picojson::array get_game_information() {
        picojson::array match_list;
        picojson::object match;

        match.insert(std::make_pair("id", picojson::value(static_cast<double>(matchID_))));
        match.insert(std::make_pair("intervalMillis", picojson::value(static_cast<double>(interval_millisecond_))));
        match.insert(std::make_pair("matchTo", picojson::value(match_name_)));
        match.insert(std::make_pair("teamID", picojson::value(static_cast<double>(teamID_[0]))));
        match.insert(std::make_pair("turnMillis", picojson::value(static_cast<double>(turn_millisecond_))));
        match.insert(std::make_pair("turns", picojson::value(static_cast<double>(max_turn_))));
        
        match_list.push_back(picojson::value(match));
        
        return match_list;
    }

    picojson::object get_game_state() {
        picojson::object result; // final return
        // actions
        {
            picojson::array history;
            for (Actions& action : actions_history_) {
                picojson::object one_action;
                one_action.insert(std::make_pair("agentID", picojson::value(static_cast<double>(action.agent_id))));
                one_action.insert(std::make_pair("dx", picojson::value(static_cast<double>(action.dx))));
                one_action.insert(std::make_pair("dy", picojson::value(static_cast<double>(action.dy))));
                one_action.insert(std::make_pair("type", picojson::value(action.type)));
                one_action.insert(std::make_pair("apply", picojson::value(static_cast<double>(action.apply))));
                one_action.insert(std::make_pair("turn", picojson::value(static_cast<double>(action.turn))));
                history.push_back(picojson::value(one_action));
            }
            result.insert(std::make_pair("actions", picojson::value(history)));
        }
        result.insert(std::make_pair("height", picojson::value(static_cast<double>(height_))));
        // points
        {
            picojson::array field_point;
            for (std::vector<Tile> &horizontal_vector : game_field_) {
                picojson::array horizontal_point;
                for (Tile &value : horizontal_vector) {
                    horizontal_point.push_back(picojson::value(static_cast<double>(value.score)));
                }
                field_point.push_back(picojson::value(horizontal_point));
            }
            result.insert(std::make_pair("points", picojson::value(field_point)));
        }
        result.insert(std::make_pair("startedAtUnixTime", picojson::value(static_cast<double>(started_unix_time_))));
        // teams
        {
            picojson::array teams;
            for (int i = 0; i < 2; i++) {
                picojson::object one_team;
                {
                    picojson::array agents;
                    for (Agent &one_agent : agent_coordinate_[i]) {
                        picojson::object agent;
                        agent.insert(std::make_pair("agentID", picojson::value(static_cast<double>(one_agent.agent_id))));
                        agent.insert(std::make_pair("x", picojson::value(static_cast<double>(one_agent.x))));
                        agent.insert(std::make_pair("y", picojson::value(static_cast<double>(one_agent.y))));
                        agents.push_back(picojson::value(agent));
                    }
                    one_team.insert(std::make_pair("agents", picojson::value(agents)));
                }
                one_team.insert(std::make_pair("areaPoint", picojson::value(static_cast<double>(area_point_calculate(teamID_[i])))));
                one_team.insert(std::make_pair("teamID", picojson::value(static_cast<double>(teamID_[i]))));
                one_team.insert(std::make_pair("tilePoint", picojson::value(static_cast<double>(tile_point_calculate(teamID_[i])))));
                teams.push_back(picojson::value(one_team));
            }
            result.insert(std::make_pair("teams", picojson::value(teams)));
        }
        // tiled
        {
            picojson::array field_tile;
            for (std::vector<Tile> &horizontal_vector : game_field_) {
                picojson::array horizontal_point;
                for (Tile &value : horizontal_vector) {
                    horizontal_point.push_back(picojson::value(static_cast<double>(value.have_team)));
                }
                field_tile.push_back(picojson::value(horizontal_point));
            }
            result.insert(std::make_pair("tiled", picojson::value(field_tile)));
        }
        result.insert(std::make_pair("turn", picojson::value(static_cast<double>(turn_))));
        result.insert(std::make_pair("width", picojson::value(static_cast<double>(width_))));
        return result;
    }

    picojson::object set_agent_actions(picojson::value input) {
        picojson::object result;
        picojson::array input_actions = input.get<picojson::object>()["actions"].get<picojson::array>();
        {
            picojson::array result_actions;
            for (picojson::array::iterator it = input_actions.begin(); it != input_actions.end(); it++) {
                picojson::object one_agent = it->get<picojson::object>();
                int agent_id = static_cast<int>(one_agent["agentID"].get<double>());
                int action_size = agent_actions_[0].size();
                bool agent_id_check = false;
                // action update
                for (int i = 0; i < action_size * 2; i++) {
                    std::vector<Actions>::iterator actions = agent_actions_[i / action_size].begin() + (i % action_size);
                    if ((*actions).agent_id == agent_id) {
                        (*actions).dx = static_cast<int>(one_agent["dx"].get<double>());
                        (*actions).dy = static_cast<int>(one_agent["dy"].get<double>());
                        (*actions).type = one_agent["type"].get<std::string>();
                        (*actions).turn = turn_;
                        agent_id_check = true;
                        break;
                    }
                }
                if (!agent_id_check) continue;
                one_agent.insert(std::make_pair("turn", picojson::value(static_cast<double>(turn_))));
                result_actions.push_back(picojson::value(one_agent));
            }
            result.insert(std::make_pair("actions", picojson::value(result_actions)));
        }

        return result;
    }


    void next_turn() {
        ++turn_;
        int action_size = agent_actions_[0].size();
        // stay overwrite
        for (int i = 0; i < action_size * 2; i++) {
            std::vector<Actions>::iterator action = agent_actions_[i / action_size].begin() + (i % action_size);
            if ((*action).type == "stay") {
                if ((*action).dx != 0 || (*action).dy != 0) (*action).apply = -1;
            }
        }

        // check next turn coordinate overlap
        for (int i = 0; i < action_size * 2; i++) {
            std::vector<Actions>::iterator first_action = agent_actions_[i / action_size].begin() + (i % action_size);
            std::vector<Agent>::iterator first_agent = agent_coordinate_[i / action_size].begin() + (i % action_size);
            int first_agent_next_x = (*first_action).dx + (*first_agent).x;
            int first_agent_next_y = (*first_action).dy + (*first_agent).y;
            if (first_agent_next_x == 0 || first_agent_next_x > width_) {
                (*first_action).apply = -1;
            }
            if (first_agent_next_y == 0 || first_agent_next_y > height_) {
                (*first_action).apply = -1;
            }
            for (int j = i + 1; j < action_size * 2; j++) {
                std::vector<Actions>::iterator second_action = agent_actions_[j / action_size].begin() + (j % action_size);
                std::vector<Agent>::iterator second_agent = agent_coordinate_[j / action_size].begin() + (j % action_size);

                int second_agent_next_x = (*second_action).dx + (*second_agent).x;
                int second_agent_next_y = (*second_action).dy + (*second_agent).y;
                if (first_agent_next_x == second_agent_next_x && first_agent_next_y == second_agent_next_y) {
                    if ((*first_action).type != "stay") (*first_action).apply = 0;
                    if ((*second_action).type != "stay") (*second_action).apply = 0;
                }
            }
        }

        // move agent
        for (int i = 0; i < action_size * 2; i++) {
            std::vector<Actions>::iterator action = agent_actions_[i / action_size].begin() + (i % action_size);
            if ((*action).apply != 1) continue;
            std::vector<Agent>::iterator agent = agent_coordinate_[i / action_size].begin() + (i % action_size);
            int agent_next_x = (*action).dx + (*agent).x;
            int agent_next_y = (*action).dy + (*agent).y;
            if ((*action).type == "move") {
                game_field_[(*agent).y - 1][(*agent).x - 1].on_agent = false;
                game_field_[agent_next_y - 1][agent_next_x - 1].have_team = teamID_[i / action_size];
                game_field_[agent_next_y - 1][agent_next_x - 1].on_agent = true;
                (*agent).x = agent_next_x;
                (*agent).y = agent_next_y;
            } else if ((*action).type == "remove") {
                game_field_[agent_next_y - 1][agent_next_x - 1].have_team = 0;
            }
        }

        // history input
        for (int i = 0; i < action_size * 2; i++) {
            std::vector<Actions>::iterator action = agent_actions_[i / action_size].begin() + (i % action_size);
            (*action).turn = turn_;
            actions_history_.push_back((*action));
            // init
            (*action).dx = 0;
            (*action).dy = 0;
            (*action).apply = 1;
            (*action).type = "stay";
            (*action).turn = turn_;
        }
        
        

    }
    
    bool end_turn() {return (turn_ == max_turn_);}
    
};