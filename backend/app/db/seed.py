import json
import os
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.db.models import University

def seed_universities():
    print("Seed verileri kontrol ediliyor...")
    
    # 1. Veritabanına bağlanmak için bir Session alıyoruz
    db: Session = SessionLocal()
    
    try:
        # 2. JSON dosyasının nerede olduğunu buluyoruz
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "universities.json")
        
        # 3. JSON dosyasını okuyoruz
        with open(json_path, "r", encoding="utf-8") as f:
            universities_data = json.load(f)
            
        added_count = 0
        
        # 4. JSON içindeki listeyi döngüye alıyoruz
        for uni_data in universities_data:
            # Bu üniversite zaten veritabanında var mı diye kontrol edelim ki duplicate (çift) olmasın
            existing_uni = db.query(University).filter(University.slug == uni_data["slug"]).first()
            
            if not existing_uni:
                # Veritabanında yoksa yeni obje oluşturup ekliyoruz
                new_uni = University(
                    name=uni_data["name"],
                    slug=uni_data["slug"],
                    mevzuat_url=uni_data["mevzuat_url"]
                    # is_crawled default olarak False gelecek (models'te öyle tanımlamıştınız)
                )
                db.add(new_uni)
                added_count += 1
            else:
                # Varsa url'nin değişip değişmediğini kontrol edip güncelliyoruz
                if existing_uni.mevzuat_url != uni_data["mevzuat_url"]:
                    existing_uni.mevzuat_url = uni_data["mevzuat_url"]
                
        # 5. Yaptığımız tüm ekleme işlemlerini commit'leyip (onaylayıp) veritabanına fiziksel olarak yazıyoruz
        db.commit()
        print(f"İşlem başarılı! {added_count} adet yeni üniversite veritabanına eklendi.")
        
    except Exception as e:
        print(f"Hata oluştu: {e}")
        db.rollback()  # Hata varsa yapılan işlemleri geri al
    finally:
        db.close() # İşimiz bitince bağlantıyı kapatıyoruz

if __name__ == "__main__":
    seed_universities()
