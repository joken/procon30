#include <boost/property_tree/json_parser.hpp>
#include <boost/foreach.hpp>
namespace beast = boost::beast;
namespace http = beast::http;
namespace net = boost::asio;
using tcp = boost::asio::ip::tcp;
namespace pt = boost::property_tree;

struct Tile {
    int score;
    bool red, blue;
};


class GameBord {
private:
    std::vector<std::vector<Tile>> game_field_;

public:
    void initalizeFieldsFromJsonFile() {
        std::cout << "Input filed json file." << std::endl;
        std::string filename;
        std::cin >> filename;
        pt::ptree pt;
        read_json(filename, pt);
        int width = pt.get_optional<int>("width").get();
        int height = pt.get_optional<int>("height").get();
        std::cout << "width: " << width << std::endl;
        std::cout << "height: " << height << std::endl;
        for (auto first_nest : pt.get_child("points")) {
            for (auto second_nest : first_nest.second.data()) {
                std::cout << second_nest << std::endl;
            }
        }
    }
};