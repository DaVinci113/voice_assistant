import lmstudio as lms

def get_response(text: str)-> str:
    model = lms.llm("qwen/qwen3-vl-4b")
    system_prompt = """Ты домашний ассистент. Отвечай достаточно коротко. Без лишних символов и смайликов. Ничего не придумывай, если не знаешь так и говори"""
    result = model.respond(text+system_prompt)

    return result

if __name__ == '__main__':
    get_response('кто ты?')