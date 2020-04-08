import asyncio
from asyncio import transports
from typing import Optional


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    # base protocol overrides
    def data_received(self, data: bytes):
        content = data.decode()
        print(content)

        if self.login is not None:
            self.send_message(content)
            self.server.msg_history.append(content)
        else:
            if content.startswith('login'):
                login = content.replace('login:', '').rstrip()

                for user in self.server.clients:
                    if user.login == login:
                        self.transport.write('This login is already taken, try another one!\n'.encode())
                        return

                self.login = login
                self.server.clients.append(self)
                self.server.send_history(self)
            else:
                self.transport.write('Invalid login message!\n'.encode())

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print('Client disconnected')

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print('New connection established')

    def send_message(self, content: str):
        message = f'{self.login}: {content.rstrip()}

        for user in self.server.clients:
            user.transport.write(message.encode())


class Server:
    clients: list
    msg_history: list
    protocol = ServerProtocol

    def __init__(self):
        self.clients = []
        self.msg_history = []

    def build_protocol(self):
        return ServerProtocol(self)

    def send_history(self, client: ServerProtocol):
        last_messages = self.msg_history[-10:]

        client.transport.write(f'Welcome, {client.login}!\n'.encode())

        for message in last_messages:
            client.transport.write(message.encode())


    async def start(self):
        loop = asyncio.get_running_loop()

        subroutine = await loop.create_server(
            protocol_factory=self.build_protocol,
            host='127.0.0.1',
            port=12234
        )
        print('Server started...')

        await subroutine.serve_forever()


def main():

    process = Server()

    try:
        asyncio.run(process.start())
    except KeyboardInterrupt:
        print('\nServer stopped manually (keyboard interrupted)')


if __name__ == '__main__':
    main()
