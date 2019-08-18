#include <boost/beast.hpp>
#include "server.cpp"
#include <cstdlib>
#include <iostream>
#include <memory>
#include <string>
#include <thread>

namespace beast = boost::beast;
namespace http = beast::http;
namespace net = boost::asio;
using tcp = boost::asio::ip::tcp;

int main() {
    try {
        auto const address = net::ip::make_address("127.0.0.1");
        auto const port = static_cast<short unsigned int>(8081);

        net::io_context ioc(1);
        tcp::acceptor accepter(ioc, tcp::endpoint(address, port));
        boost::system::error_code error;
        while(true) {
            tcp::socket socket(ioc);
            accepter.accept(socket, error);
            std::thread{std::bind(
                &server_session,
                std::move(socket))}.detach();
            std::cout << error << std::endl;
        }
    } catch (std::exception &e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return EXIT_FAILURE;
    }
}