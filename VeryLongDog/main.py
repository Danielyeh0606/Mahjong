from verylongdog import *
if __name__ == "__main__":
    AI = VeryLongDog()
    while True:
        command = input().split()
        # print(command)
        # command = command.split()
        match command[0]:
            case '/ready':
                print("/ready")
            case '/start':
                AI.DealStart(int(command[2]))
            case '/initCard':
                tile_list = [int(tile) for tile in command[1:]]
                AI.initCard(tile_list)
            case '/throw':
                AI.MakeThrow(int(command[1]), int(command[2]))
            case '/ask':
                AI.DealAsk(command)
            case '/mo':		    
                AI.DealMo(command[1])
            case '/exit':
                break
