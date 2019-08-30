#include <boost/property_tree/json_parser.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/ini_parser.hpp>
#include "game_bord.cpp"
namespace beast = boost::beast;
namespace http = beast::http;
namespace net = boost::asio;
using tcp = boost::asio::ip::tcp;
namespace pt = boost::property_tree;

std::string ptreeToString(pt::ptree ptree) {
    std::stringstream ss;
    write_json(ss, ptree);
    return ss.str();
};

template<class Body, class Allocator,class Send, class GameBord> void
handleRequest(http::request<Body, http::basic_fields<Allocator>>&& req, Send&& send, GameBord* gamebord)
{
    auto const response =
    [&req](http::status status, pt::ptree sent_json) {
        http::response<http::string_body> res{status, req.version()};
        res.set(http::field::content_type, "application/json");
        res.keep_alive(req.keep_alive());
        res.body() = ptreeToString(sent_json);
        res.content_length(res.body().size());
        res.prepare_payload();
        return res;
    };

    if (req.target() == "/matches") {
        pt::ptree ptree;
        ptree.put("status", "OK");
        std::cout << "Status: get Match" << std::endl;
        return send(response(http::status::ok, ptree));
    } else {
        pt::ptree ptree;
        ptree.put("status", "Invalid URL");
        std::cout << "Status: Invalid URL" << std::endl;
        return send(response(http::status::bad_request, ptree));
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

    handleRequest(std::move(req), lambda, gamebord);
    socket.shutdown(tcp::socket::shutdown_send, ec);
}