import lmstudio as lms

def get_response(text: str)-> str:
    model = lms.llm("qwen/qwen3-vl-4b")
    result = model.respond(text)

    return result

if __name__ == '__main__':
    get_response('кто ты?')