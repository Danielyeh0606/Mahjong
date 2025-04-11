import random
import redis
import rapidjson as rjson

class VeryLongDog():
    def __init__(self):
        self.mySeat = int()
        self.openSeat = int()
        self.privateHand = PrivateHand()
        self.publicHand = PublicHand()
        self.tool = Tool(self.privateHand, self.publicHand)
        self.now_discard = 0
    
    def DealStart(self, myseat):
        self.mySeat = myseat
        
    def initCard(self, tile_list):
        self.privateHand.Hand = tile_list
        for tile in tile_list:
            self.publicHand.remain[tile // 100 - 1][tile // 10 % 10 - 1] -= 1
        
    def DealAsk(self, command):
        match command[1]:
            case 'throw':
                tile = random.choice(self.tool.getDiscard())
                print("/throw", tile)
            case 'hu':
                print("/hu")
            case _:
                print("/pass")
    
    def DealMo(self, tile):
        self.privateHand.Hand.append(tile)
    
    def MakeThrow(self, player, tile):
        self.publicHand.remain[tile // 100 - 1][tile // 10 % 10 - 1] -= 1
        self.publicHand.Discard[player - 1][tile // 100 - 1][tile // 10 % 10 - 1] += 1
        if player == self.mySeat:
            self.privateHand.Hand.remove(tile)
        
    def MakeEat(self, player, tile_list):
        pass
    
    def MakePong(self, player, tile_list):
        pass
    
    def MakeGong(self, player, case, tile_list):
        pass
    
    def DealThrow(self):
        discard_list = self.tool.getDiscard()
        discard_list = self.tool.AllPossibleSearch(discard_list)
        tile = random.choice(discard_list)
        print("/throw", tile)
        
    def DealEat(self):
        pass
    
    def DealPong(self):
        pass
    
    def DealGong(self):
        pass
    
    
class PrivateHand():
    def __init__(self):
        self.Hand = []
        self.single = []
        self.nDA = [] #[group_list][tile_list]
        self.eye = []
        self.DA = []
        self.rely = []
    
    def sortHand(self):
        self.DA.clear()
        self.eye.clear()
        self.nDA.clear()
        self.rely.clear()
        self.single.clear()
        self.Hand.sort()

        suit= [[] for _ in range(4)]
        for tile in self.Hand:
            suit[(tile // 100) - 1].append(tile)
        
        temp_rely = []
        for s in range(4): #將相依關係劃分區隔(ex. 11 12 12 | 22 23 | 26 26 | 34 35 37 | 42 | 43)
            temp = []
            if len(suit[s]) == 0:
                continue
            else:
                temp.append(suit[s][0])
            for t in range(1, len(suit[s])):
                if s == 3 and (suit[s][t - 1] // 10) != (suit[s][t] // 10): #字牌
                    temp_rely.append(temp[:])
                    temp.clear()
                elif (suit[s][t - 1] // 10) + 2 < (suit[s][t] // 10):
                    temp_rely.append(temp[:])
                    temp.clear()
                temp.append(suit[s][t])
            temp_rely.append(temp[:])
        
        for rely in temp_rely: #分類
            if len(rely) == 1: #single
                self.single.append(rely[0])
            elif len(rely) == 3: #DA
                if rely[0] // 10 == rely[1] // 10 == rely[2] // 10:
                    self.DA.append(rely)
                elif rely[0] // 10 + 1 == rely[1] // 10 == rely[2] // 10 - 1:
                    self.DA.append(rely)
                else:
                    self.rely.append(rely)
            elif len(rely) == 2: #nDA, eye
                if rely[0] // 10 == rely[1] // 10:
                    self.eye.append(rely)
                else:
                    self.nDA.append(rely)
            else: #rely
                self.rely.append(rely)
    
        
    
class PublicHand():
    def __init__(self):
        self.ShowHand = [[[]] for _ in range(4)] #[player][group_list][tile_list]
        self.Discard = [[[0 for _ in range(9)] for _ in range(4)] for _ in range(4)] #[player][suit][number]
        self.remain = [[4 for _ in range(9)] for _ in range(4)] #[suit][number]
        self.remain[3][7] = self.remain[3][8] = 0
    
    
class Tool():
    def __init__(self, privateHand, publicHand):
        self.privateHand = privateHand
        self.publicHand = publicHand
        self.relyTable = RelyTable()
        
    def getGroupScore(self, group):
        #type{eye, hole, sequence}
        if group[0] // 10 == group[1] // 10: #eye
            type = 1
        elif group[0] // 10 + 2 == group[1] // 10: #hole
            type = 2
        else: #sequence
            type = 3

        score = 0
        suit = group[0] // 100
        if type == 1:
            number = group[0] // 10 % 10
            score += self.publicHand.remain[suit - 1][number - 1]
            score = score * 2 + 1;#weight of eye
        elif type == 2:
            number = group[0] // 10 % 10 + 1
            score += self.publicHand.remain[suit - 1][number - 1]
        elif type == 3:
            number = group[0] // 10 % 10 - 1
            if number > 0:
                score += self.publicHand.remain[suit - 1][number - 1]
            number = group[1] // 10 % 10 + 1
            if number < 10:
                score += self.publicHand.remain[suit - 1][number - 1];    
        
        return score
    
    def getHandScore(self, group_list):
        result = 0
        for group in group_list:
            if len(group) == 3:
                result += 100
            elif len(group) == 2:
                if(group[0] // 10 == group[1] // 10):
                    result += 10
                else:
                    result += 1
        return result
    
    def getNumInHu(self, tile_list):
        
        if isinstance(tile_list, list):
            hand = PrivateHand()
            hand.Hand = tile_list
            hand.sortHand()
        else:
            hand = tile_list
        
        targetDA = len(hand.Hand) // 3
        score = self.getHandScore(hand.nDA + hand.eye + hand.DA)
        for rely in hand.rely:
            score += self.relyTable.getRelyScore(rely)
        
        differ = targetDA - (score // 100)
        if score // 10 % 10 > 1:
            eye_to_nDA = score // 10 % 10 - 1
            score = score - (eye_to_nDA * 10) + eye_to_nDA
        
        out = 0
        if differ > 0:
            if differ > score % 10: 
                temp = score % 10
            else:
                temp = differ
            out += temp + (differ - temp) * 2
        
        if score // 10 % 10 == 0:
            out += 1

        return out
    
    def findEye(self):
        out_index = -1
        min_loss = 100
        for index in range(len(self.privateHand.rely)):
            rely = self.privateHand.rely[index]
            set_list = self.relyTable.getRelySet(rely)
            max_score = 0
            max_has_eye_score = -1
            max_score_set = []
            same_set = False
            for set in set_list:
                score, has_eye = self.getRelySetTotalGroupScore(set, return_has_eye=True)
                if score > max_score:
                    max_score = score
                    max_score_set = set
                    same_set = False
                    
                if has_eye:
                    if score > max_has_eye_score:
                        max_has_eye_score = score
                        same_set = (set == max_score_set)
            
            if max_has_eye_score != -1: #rely has eye
                loss = max_score - max_has_eye_score
                print(index, ":", max_score, max_has_eye_score, same_set)
                if loss < min_loss:
                    min_loss = loss
                    out_index = index
                elif loss == min_loss:
                    if same_set:
                        out_index = index
            
        return out_index
            
                    
    def getRelySetTotalGroupScore(self, set, return_has_eye):
        sum = 0
        has_eye = False
        for group in set:
            if len(group) == 2:
                sum += self.getGroupScore(group)
                
                #find eye
                if return_has_eye and group[0] // 10 == group [1] // 10:
                    has_eye = True
        return sum, has_eye
    
    def getRelyBestSet(self, set_list, need_eye):
        best_list = []
        max_score = 0
        for index in range(len(set_list)):
            set = set_list[index]
            score, has_eye = self.getRelySetTotalGroupScore(set, return_has_eye=need_eye)
            if not need_eye or (need_eye and has_eye):
                if score > max_score:
                    max_score = score
                    best_list = [index]
                elif score == max_score:
                    best_list.append(index)
           
        return best_list
    
    def getRelySetDiscard(self, set, need_eye):
        single = []
        nDA = []
        eye = []
        for group in set:
            if len(group) == 1:
                single.append(group[0])
            elif len(group) == 2:
                if group[0] // 10 == group[1] // 10:
                    eye.append(group)
                else:
                    nDA.append(group)
        if len(single) != 0:
            return single
        else:
            discard_list = []
            min_score = 10
            group_list = nDA
            if not need_eye or len(eye) > 1:
                group_list += eye
            for group in group_list:
                score = self.getGroupScore(group)
                if score < min_score:
                    min_score = score
                    discard_list = [group[0], group[1]]
                else:
                    discard_list.append(group[0])
                    discard_list.append(group[1])
            return discard_list
    
    def getRelyDiscard(self, tile_list, need_eye):
        set_list = self.relyTable.getRelySet(tile_list)
        best_list = self.getRelyBestSet(set_list, need_eye)
        discard_list = []
        for index in best_list:
            discard_list += self.getRelySetDiscard(set_list[index], need_eye)
        
        return discard_list
            
            
    def getDiscard(self):
        self.privateHand.sortHand()
        discard_list = []
        
        hand_score = self.getHandScore(self.privateHand.nDA + self.privateHand.eye + self.privateHand.DA)
        for rely in self.privateHand.rely:
            hand_score += self.relyTable.getRelyScore(rely)
        hand_score +=  (17 - len(self.privateHand.Hand)) // 3 * 100
        
        #exception
        if hand_score == 500 and len(self.privateHand.single) == 1: #散牌只有一張, 相依牌牌群裡有散牌
            discard_list = self.privateHand.single[:]
            for rely in self.privateHand.rely:
                discard_list += self.getRelyDiscard(rely, need_eye=False)
        #散牌優先
        elif len(self.privateHand.single) != 0:
            #散牌棄牌排序
            maxOrder = 0
            for tile in self.privateHand.single:
                order = 0
                if tile // 100 == 4: #是否是字
                    order += 1000
                    if tile // 10 % 10 > 4: #是否為中發白
                        order += 10
                    else:
                        order += 20
                
                num_of_throw = 0
                for i in range(4):
                    num_of_throw += self.publicHand.Discard[i][tile // 100 - 1][tile // 10 % 10 - 1]
                order += num_of_throw * 100; #已打張數
                
                if tile // 100 != 4: #邊張
                    order += abs(tile // 10 % 10 - 5)

                if order > maxOrder:
                    maxOrder = order
                    discard_list = [tile]
                elif order == maxOrder:
                    discard_list.append(tile)
        else: #未成搭 及 相依牌群 棄牌
            #未成搭、眼
            min_score = 10
            group_list = self.privateHand.nDA
            nDA_discard_lsit = []
            if len(self.privateHand.eye) > 1:
                group_list += self.privateHand.eye
            for group in group_list:
                score = self.getGroupScore(group)
                if score < min_score:
                    min_score = score
                    nDA_discard_lsit = [group[0], group[1]]
                if score == min_score:
                    nDA_discard_lsit.append(group[0])
                    nDA_discard_lsit.append(group[1])
            
            #未成搭棄牌排序
            maxOrder = 0
            for tile in nDA_discard_lsit:
                order = 10
                if tile // 100 == 4: #是否是字
                    order -= 10
                    if tile // 10 % 10 > 4: #是否為中發白
                        order += 1
                    else:
                        order += 2

                num_of_throw = 0
                for i in range(4):
                    num_of_throw += self.publicHand.Discard[i][tile // 100 - 1][tile // 10 % 10 - 1]
                order += num_of_throw * 100; #已打張數
                
                if tile // 100 != 4: #邊張
                    order += abs(tile // 10 % 10 - 5)


                if order > maxOrder:
                    maxOrder = order
                    discard_list = [tile]
                elif order == maxOrder:
                    discard_list.append(tile)
            
            #相依牌群棄牌
            if len(self.privateHand.eye) == 0: #沒有眼的情況，從相依牌群中找眼
                eye_index = self.findEye()
                for index in range(len(self.privateHand.rely)):
                    rely = self.privateHand.rely[index]
                    if eye_index == index:
                        discard_list += self.getRelyDiscard(rely, need_eye=True)
                    else:
                        discard_list += self.getRelyDiscard(rely, need_eye=False)
            else:
                discard_list += self.getRelyDiscard(rely, need_eye=False)
            
        
        #exception
        if hand_score == 501: #將刻子拆成眼
            hand = self.privateHand.Hand
            if len(hand) >= 5:
                for i in range(len(hand) - 2):
                    if hand[i] // 10 == hand[i + 1] // 10 == hand[i + 2] // 10:
                        discard_list.append(hand[i])
                        i += 2
        
        #刪除相同牌
        discard_list.sort()
        out = [discard_list[0]]
        for i in range(1, len(discard_list)):
            if discard_list[i] // 10 != discard_list[i - 1] // 10:
                out.append(discard_list[i]) 
        
        #找正確編號
        index = 0
        for tile in self.privateHand.Hand:
            if tile // 10 == out[index] // 10:
                out[index] = tile
                index += 1
                if index == len(out):
                    break
        
        return out
            
    def AllPossibleSearch(self, discard_set):
        base = 20
        filter_set = []

        #以進胡數刪去選項
        for tile in discard_set:
            temp_hand = self.privateHand.Hand[:]
            temp_hand.remove(tile)
            score = self.getNumInHu(temp_hand)

            if score < base:
                filter_set = [tile]
                base = score
            elif score == base:
                filter_set.append(tile)
            
        out = []
        MaxSum = 0
        #test 34 possibilities
        for tile in filter_set:
            new_hand = self.privateHand.Hand[:]
            new_hand.remove(tile)
            
            sum = 0
            for mo_tile in range(110, 480, 10):# 34 possibilities
                if mo_tile % 100 == 0:
                    continue
                if self.publicHand.remain[mo_tile // 100 - 1][mo_tile // 10 % 10 - 1] == 0:
                    continue
                
                hand = PrivateHand()
                hand.Hand = new_hand[:]
                hand.Hand.append(mo_tile)
                hand.sortHand()
                if mo_tile in hand.single:   #進手牌後為孤張 => 與進牌前進胡數相同
                    continue
                elif self.getNumInHu(hand) < base:
                    sum += self.publicHand.remain[mo_tile // 100 - 1][mo_tile // 10 % 10 - 1]
                
            if sum > MaxSum:
                MaxSum = sum
                out = [tile]
            elif MaxSum == sum:
                out.append(tile)

        return out
    
    
    
    
class RelyTable():
    def __init__(self):
        self.redis_database = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.rjson_score = [0, 0, 0]
        self.rjson_set = [0, 0, 0]
        for i in range(3, 14):
            with open("RelyTable/originalScoreTable/" + str(i) + "_Size_Table.json", "r", encoding="utf-8") as file:
                data = rjson.load(file)
                self.rjson_score.append(data)
            with open("RelyTable/originalSetTable/" + str(i) + "_Size_Set_Table.json", "r", encoding="utf-8") as file:
                data = rjson.load(file)
                self.rjson_set.append(data)
        
    def getRelyScore(self, tile_list):
        key = ""
        for tile in tile_list:
            key += str(tile // 10 - tile_list[0] // 10 + 1)
        if(len(key) < 14):
            return self.rjson_score[len(key)][key]
        else:
            return int(self.redis_database.hget(key, "score"))
        
        
    def getRelySet(self, tile_list):
        key = ""
        for tile in tile_list:
            key += str(tile // 10 - tile_list[0] // 10 + 1)
        if(len(key) < 14):
            set_list = self.rjson_set[len(key)][key]
        else:
            set_list = rjson.loads(self.redis_database.hget(key, "set"))
        
        out = []
        for set in set_list:
            temp_s = []
            for group in set:
                temp_g = []
                for i in range(len(group)):
                    temp_g.append(tile_list[0] - 10 + (int(group[i]) * 10))
                temp_s.append(temp_g)
            out.append(temp_s)
        
        return out
        
    def __del__(self):
        self.redis_database.close()
        
        
#test
'''
s = "110 120 130 221 220 222 320 340"
a = PrivateHand()
a.Hand = [int(item) for item in s.split()]

b = PublicHand()
for tile in a.Hand:
    suit = tile // 100
    number = tile // 10 % 10
    b.remain[suit - 1][number - 1] -= 1
    
for _ in range(20):
    player = random.choice(range(4))
    suit = random.choice(range(4))
    number = random.choice(range(9))
    if b.remain[suit][number] > 0:
        b.remain[suit][number] -= 1
        b.Discard[player][suit][number] += 1

tool = Tool(a, b)

print("remain:")
print("   1 2 3 4 5 6 7 8 9")
print("--------------------")
for s in range(4):
    print(f"{s + 1}|", end="")
    for n in range(9):
        print(f" {tool.publicHand.remain[s][n]}", end="")
    print()
print()


print("discard:")
print("   1 2 3 4 5 6 7 8 9")
print("--------------------")
for s in range(4):
    print(f"{s + 1}|", end="")
    for n in range(9):
        print(f" {sum([d[s][n] for d in tool.publicHand.Discard])}", end="")
    print()
print()

print("Hand: ", end="")
for tile in tool.privateHand.Hand:
    print(tile, end=" ")
print("\n")

print(f"In Hu: {tool.getNumInHu(tool.privateHand.Hand)}\n")

tool.privateHand.sortHand()
print("single:")
for s in tool.privateHand.single:
    print(s, end=" ")
print("\neye:")
for s in tool.privateHand.eye:
    print(s, tool.getGroupScore(s), end=" ")
print("\nnDA:")
for s in tool.privateHand.nDA:
    print(s, tool.getGroupScore(s), end=" ")
print("\nDA:")
for s in tool.privateHand.DA:
    print(s, end=" ")

print("\n")

need_eye = False
need_eye = len(tool.privateHand.eye) == 0
print("\nNeed eye:", need_eye)
eye_index = -1
if need_eye:
    eye_index = tool.findEye()  
print("Eye index:", eye_index)


print("\nrely: ")
for i in range(len(tool.privateHand.rely)):
    s = tool.privateHand.rely[i]
    print(s, ": ")
    print("best set: ")
    set_list = tool.relyTable.getRelySet(s)
    index_list =  tool.getRelyBestSet(set_list, eye_index == i)
    for set_index in index_list:
        print(set_list[set_index], end=": ")
        for d_tile in tool.getRelySetDiscard(set_list[set_index], i == eye_index):
            print(d_tile, end=" ")
    print("\n")
    
print("Discard:")
for tile in tool.getDiscard():
    print(tile, end=" ")
print("\n")

for tile in tool.AllPossibleSearch(tool.getDiscard()):
    print(tile, end=" ")
print("\n")
'''    