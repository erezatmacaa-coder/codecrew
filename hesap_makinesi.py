def toplama(x, y):
    return x + y

def cikarma(x, y):
    return x - y

def carpma(x, y):
    return x * y

def bolme(x, y):
    if y == 0:
        return "Hata: Bölme işlemi sıfıra yapılamaz!"
    else:
        return x / y

def main():
    print("Hesap Makinesi")
    print("1. Toplama")
    print("2. Çıkarma")
    print("3. Çarpma")
    print("4. Bölme")
    
    choice = input("İşlem seçiniz (1/2/3/4): ")
    
    if choice in ('1', '2', '3', '4'):
        num1 = float(input("İlk sayıyı giriniz: "))
        num2 = float(input("İkinci sayıyı giriniz: "))
        
        if choice == '1':
            print(num1, "+", num2, "=", toplama(num1, num2))
        elif choice == '2':
            print(num1, "-", num2, "=", cikarma(num1, num2))
        elif choice == '3':
            print(num1, "*", num2, "=", carpma(num1, num2))
        elif choice == '4':
            print(num1, "/", num2, "=", bolme(num1, num2))
    else:
        print("Geçersiz seçim")

if __name__ == "__main__":
    main()