from pipeline import compiled_graph

def main():
    print("initializing...")

    initial_state = {}

    try:
        result = compiled_graph.invoke(initial_state)
        print("------completed-------")
    except Exception as e:
        print("failed")

if __name__ == "__main__":
    main()