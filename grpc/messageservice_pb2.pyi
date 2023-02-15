from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LoginResponse(_message.Message):
    __slots__ = ["messages", "statusCode"]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    STATUSCODE_FIELD_NUMBER: _ClassVar[int]
    messages: _containers.RepeatedCompositeFieldContainer[Message]
    statusCode: str
    def __init__(self, statusCode: _Optional[str] = ..., messages: _Optional[_Iterable[_Union[Message, _Mapping]]] = ...) -> None: ...

class Message(_message.Message):
    __slots__ = ["message", "sender"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SENDER_FIELD_NUMBER: _ClassVar[int]
    message: str
    sender: str
    def __init__(self, sender: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class MessageRequest(_message.Message):
    __slots__ = ["message", "receiver", "sender"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_FIELD_NUMBER: _ClassVar[int]
    SENDER_FIELD_NUMBER: _ClassVar[int]
    message: str
    receiver: str
    sender: str
    def __init__(self, sender: _Optional[str] = ..., receiver: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class SearchRequest(_message.Message):
    __slots__ = ["query"]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    query: str
    def __init__(self, query: _Optional[str] = ...) -> None: ...

class SearchResponse(_message.Message):
    __slots__ = ["results", "statusCode"]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    STATUSCODE_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedScalarFieldContainer[str]
    statusCode: str
    def __init__(self, statusCode: _Optional[str] = ..., results: _Optional[_Iterable[str]] = ...) -> None: ...

class StatusCodeResponse(_message.Message):
    __slots__ = ["statusCode"]
    STATUSCODE_FIELD_NUMBER: _ClassVar[int]
    statusCode: int
    def __init__(self, statusCode: _Optional[int] = ...) -> None: ...

class UsernameRequest(_message.Message):
    __slots__ = ["username"]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...
