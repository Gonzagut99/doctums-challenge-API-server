import uuid

def generate_uuid_from_text(text: str) -> str:
    namespace = uuid.NAMESPACE_DNS
    return str(uuid.uuid5(namespace, text))


def generate_uuid4() -> str:
    return str(uuid.uuid4())