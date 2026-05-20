import math

def calculate_area(radius):
    if radius < 0:
        raise ValueError("Radius cannot be negative")
    return math.pi * radius ** 2

# Example usage
if __name__ == "__main__":
    try:
        radius = float(input("Enter the radius of the circle: "))
        area = calculate_area(radius)
        print(f"The area of the circle with radius {radius} is: {area}")
    except ValueError as e:
        print(e)       