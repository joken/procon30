#include <boost/property_tree/json_parser.hpp>

struct Tile {
    int score;
    bool red, blue;
};


class GameBord {
private:
    std::vector<std::vector<Tile>> game_field_;
    int a = 3;
public:
 };