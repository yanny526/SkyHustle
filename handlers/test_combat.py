from modules.combat_manager import calculate_power, attack_player

# 1) Power test
print("=== Power Test ===")
# (Make sure your “Army” sheet has TEST1/user “TEST1” with 3 infantry,2 tanks,1 artillery)
p = calculate_power("TEST1")
print("calculate_power('TEST1') ➞", p, "(expect 230)")

# 2) Attack test
print("\n=== Attack Test ===")
# (Make sure your “Players” sheet has A with 100 credits, B with 50)
out = attack_player("A", "B")
print("attack_player('A','B') ➞", out)
