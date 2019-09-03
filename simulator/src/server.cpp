#include <boost/property_tree/json_parser.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/ini_parser.hpp>
#include <utility>
#include "game_bord.cpp"
#include "picojson.h"
namespace beast = boost::beast;
namespace http = beast::http;
namespace net = boost::asio;
using tcp = boost::asio::ip::tcp;
namespace pt = boost::property_tree;

std::string picojson_to_string(picojson::object obj) {
    picojson::value val(obj);
    return val.serialize();
};

// method over load
std::string picojson_to_string(picojson::array arr) {
    picojson::value val(arr);
    return val.serialize();
}

template<class Body, class Allocator,class Send, class GameBord> void
handle_request(http::request<Body, http::basic_fields<Allocator>>&& req, Send&& send, GameBord* gamebord)
{
    auto const object_response =
    [&req](http::status status, picojson::object sent_json) {
        http::response<http::string_body> res{status, req.version()};
        res.set(http::field::content_type, "application/json");
        res.keep_alive(req.keep_alive());
        res.body() = picojson_to_string(std::move(sent_json));
        res.content_length(res.body().size());
        res.prepare_payload();
        return res;
    };

    auto const array_response =
    [&req](http::status status, picojson::array sent_json) {
        http::response<http::string_body> res{status, req.version()};
        res.set(http::field::content_type, "application/json");
        res.keep_alive(req.keep_alive());
        res.body() = picojson_to_string(std::move(sent_json));
        res.content_length(res.body().size());
        res.prepare_payload();
        return res;
    };
    
    picojson::object result_json;
    if (req.method() == http::verb::post) {
        if (req.target() == "/matches/1/action") {
            std::cout << "Status: post action" << std::endl;
            std::cout << req.body() << std::endl;
            picojson::value input_json;
            picojson::parse(input_json, req.body());
            return send(object_response(http::status::ok, gamebord->set_agent_actions(input_json)));
        } else {
            result_json.insert(std::make_pair("status", "Invalid URL"));
            std::cout << "Status: Invalid URL" << std::endl;
            return send(object_response(http::status::bad_request, result_json));
        }
    }

    // get request
    if (req.target() == "/ping") {
        result_json.insert(std::make_pair("status", "OK"));
        std::cout << "Status: get Ping" << std::endl;
        return send(object_response(http::status::ok, result_json));
    } else if (req.target() == "/matches") {
        std::cout << "Status: get game information acquisition" << std::endl;
        return send(array_response(http::status::ok, gamebord->get_game_information()));
    } else if (req.target() == "/matches/1") {
        std::cout << "Status: get match" << std::endl;
        return send(object_response(http::status::ok, gamebord->get_game_state()));
    } else if (req.target() == "/favicon.ico" ) {
        result_json.insert(std::make_pair("status", "Favicon is not found."));
        std::cout << "Status: Can not get favicon" << std::endl;
        return send(object_response(http::status::not_found, result_json));
    } else {
        result_json.insert(std::make_pair("status", "Invalid URL"));
        std::cout << "Status: Invalid URL" << std::endl;
        return send(object_response(http::status::bad_request, result_json));
    }
    std::cout << req.target() << std::endl;
}

template<class Stream> struct send_lambda {
    Stream& stream_;
    beast::error_code& ec_;
    explicit send_lambda(
        Stream& stream,
        beast::error_code& ec)
        : stream_(stream)
        , ec_(ec)
    {}

    template<bool isRequest, class Body, class Fields> void operator()(http::message<isRequest, Body, Fields>&& msg) const {
        http::serializer<isRequest, Body, Fields> sr{msg};
        http::write(stream_, sr, ec_);
    }
};

// HTTP server connect
void serverSession(tcp::socket& socket, GameBord* gamebord) {
    beast::error_code ec;
    beast::flat_buffer buffer;
    send_lambda<tcp::socket> lambda{socket, ec};

    http::request<http::string_body> req;
    http::read(socket, buffer, req, ec);

    handle_request(std::move(req), lambda, gamebord);
    socket.shutdown(tcp::socket::shutdown_send, ec);
}

void game_progress(GameBord* gamebord) {
    int now_unix_time = time(nullptr);
    bool game_start = false;
    std::chrono::high_resolution_clock::time_point start_clock;
    std::chrono::milliseconds elapsed_time;
    int end_turn_millisecond = gamebord->get_interval_millisecond() + gamebord->get_turn_millisecond();
    bool progress_flag = false;
    while(true) {
        now_unix_time = time(nullptr);
        if (now_unix_time - gamebord->get_started_unix_time() == 0 && !game_start) {
            start_clock = std::chrono::high_resolution_clock::now();
            game_start = true;
        }
        if (!game_start) continue; // under code run if game start

        elapsed_time = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now() - start_clock);
        if (elapsed_time.count() >= gamebord->get_interval_millisecond()) {
            if (!progress_flag) {
                std::cout << "next turn" << std::endl;
                gamebord->next_turn();
                progress_flag = true;
            }
            if (elapsed_time.count() >= end_turn_millisecond) {
                start_clock = std::chrono::high_resolution_clock::now();
                progress_flag = false;
            } 
        }
        if (gamebord->end_turn()) break;
    }
}