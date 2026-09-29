import ngrok

listener = ngrok.forward(5000, proto="http")

print("Publikus cím:")
print(listener.url())

input("Enter a leállításhoz...")