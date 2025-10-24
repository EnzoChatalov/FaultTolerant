import uuid

class Message:
    def init(self, msg_type, content, sender_id):
        self.msg_type = msg_type
        self.content = content
        self.sender_id = sender_id
        self.id = str(uuid.uuid4())
