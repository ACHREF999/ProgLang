# first line of `code` towards a goal
import jingo

while True:
    text = input('jingo >')
    if text.strip() == "" : continue
    result, error = jingo.run('<stdin>', text)
    if error:
        print(error.as_string())
    # basically if there is only an if /elif statements and none of the cases got executed then the interpreter would return None
    elif result:
        if len(result.elements) == 1 :
            print(result.elements[0])
        else:
            print(result )
