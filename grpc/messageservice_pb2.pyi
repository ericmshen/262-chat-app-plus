from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Message(_message.Message):
    __slots__ = ["body", "receiver", "sender", "timestamp"]
    BODY_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_FIELD_NUMBER: _ClassVar[int]
    SENDER_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    body: str
    receiver: str
    sender: str
    timestamp: int
    def __init__(self, sender: _Optional[str] = ..., receiver: _Optional[str] = ..., timestamp: _Optional[int] = ..., body: _Optional[str] = ...) -> None: ...

class MessageRequest(_message.Message):
    __slots__ = ["receiver"]
    RECEIVER_FIELD_NUMBER: _ClassVar[int]
    receiver: str
    def __init__(self, receiver: _Optional[str] = ...) -> None: ...

class MessageResponse(_message.Message):
    __slots__ = ["messages"]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    messages: _containers.RepeatedCompositeFieldContainer[Message]
    def __init__(self, messages: _Optional[_Iterable[_Union[Message, _Mapping]]] = ...) -> None: ...

class Status(_message.Message):
    __slots__ = ["code", "error"]
    CODE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    code: int
    error: str
    def __init__(self, code: _Optional[int] = ..., error: _Optional[str] = ...) -> None: ...
