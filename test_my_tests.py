def test_always_passes():
    assert True

def test_always_fails():
    assert True
    
def addition(num1, num2):
    return num1+num2

def test_addition():
    assert addition(1, 2) == 3