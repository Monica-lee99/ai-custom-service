import base64
import hashlib
import hmac
import random
import struct
import time


VERSION = "001"


class Privileges:
    PRIV_PUBLISH_STREAM = 0
    PRIV_PUBLISH_AUDIO_STREAM = 1
    PRIV_PUBLISH_VIDEO_STREAM = 2
    PRIV_PUBLISH_DATA_STREAM = 3
    PRIV_SUBSCRIBE_STREAM = 4


class ByteBuf:
    def __init__(self):
        self.buffer = bytearray()

    def put_uint16(self, value):
        self.buffer.extend(struct.pack("<H", int(value)))
        return self

    def put_uint32(self, value):
        self.buffer.extend(struct.pack("<I", int(value)))
        return self

    def put_bytes(self, value):
        self.put_uint16(len(value))
        self.buffer.extend(value)
        return self

    def put_string(self, value):
        return self.put_bytes(str(value).encode())

    def put_tree_map_uint32(self, value):
        if not value:
            self.put_uint16(0)
            return self

        self.put_uint16(len(value))
        for key in sorted(value.keys(), key=int):
            self.put_uint16(int(key))
            self.put_uint32(value[key])
        return self

    def pack(self):
        return bytes(self.buffer)


class AccessToken:
    def __init__(self, app_id, app_key, room_id, user_id, nonce=None, issued_at=None):
        self.app_id = app_id
        self.app_key = app_key
        self.room_id = room_id
        self.user_id = user_id
        self.issued_at = int(issued_at if issued_at is not None else time.time())
        self.nonce = int(nonce if nonce is not None else random.getrandbits(32))
        self.expire_at = 0
        self.privileges = {}

    def add_privilege(self, privilege, expire_timestamp):
        self.privileges[int(privilege)] = int(expire_timestamp)

        if privilege == Privileges.PRIV_PUBLISH_STREAM:
            self.privileges[Privileges.PRIV_PUBLISH_VIDEO_STREAM] = int(expire_timestamp)
            self.privileges[Privileges.PRIV_PUBLISH_AUDIO_STREAM] = int(expire_timestamp)
            self.privileges[Privileges.PRIV_PUBLISH_DATA_STREAM] = int(expire_timestamp)

    def expire_time(self, expire_timestamp):
        self.expire_at = int(expire_timestamp)

    def pack_msg(self):
        return (
            ByteBuf()
            .put_uint32(self.nonce)
            .put_uint32(self.issued_at)
            .put_uint32(self.expire_at)
            .put_string(self.room_id)
            .put_string(self.user_id)
            .put_tree_map_uint32(self.privileges)
            .pack()
        )

    def serialize(self):
        message = self.pack_msg()
        signature = hmac.new(
            self.app_key.encode(),
            message,
            hashlib.sha256,
        ).digest()
        content = ByteBuf().put_bytes(message).put_bytes(signature).pack()
        return VERSION + self.app_id + base64.b64encode(content).decode()
