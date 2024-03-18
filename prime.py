Args:
    n (int): The number to be checked.

Returns:
    bool: True if the number is prime, False otherwise.
"""
if n < 2:
    return False
for i in range(2, int(n ** 0.5) + 1):
    if n % i == 0:
        return False
return True
