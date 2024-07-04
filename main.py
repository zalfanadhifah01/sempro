from process import preparation,generate_response
from flask import Flask,render_template,request,redirect,url_for,jsonify,session
from skin_detection import predict_skin
import os,json,uuid,time
from PIL import Image
from io import BytesIO
import exifread
# download nltk
preparation()

#Start Chatbot
app = Flask(__name__)
list_products = [
    {
        "id": 1,
        "nama": "ACNE Treatment",
        "harga": "IDR 155k ~ 420k",
        "deskripsi": "Perawatan ini ditujukan untuk mengatasi masalah jerawat dengan berbagai metode" +
                " yang efektif untuk membersihkan kulit, mengurangi peradangan, dan mencegah ti" +
                "mbulnya jerawat baru.",
        "gambar": "/static/image/treatment_1.jpg",
        "rating": "52,912",
        "review": "4,01",
        "discount": "36",
        "limited_discount": [
            "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                    "nsaction, syarat dan ketentuan berlaku"
        ],
        "key_highlight": [
            "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
        ],
        "spesification": [
            {
                "nama": "Photodinamic Therapy",
                "harga": "155k"
            }, {
                "nama": "Oxygen",
                "harga": "210k"
            }, {
                "nama": "Chemical Peeling Acne",
                "harga": "285k"
            }, {
                "nama": "Oxy + Pdt",
                "harga": "240k"
            }, {
                "nama": "Peeling + Pdt",
                "harga": "320k"
            }, {
                "nama": "Peeling + Oxy",
                "harga": "385k"
            }, {
                "nama": "Peeling + Pdt + Oxy",
                "harga": "420k"
            }
        ]
    }, {
        "id": 2,
        "nama": "GLOWING/BRIGHTENING Treatment",
        "deskripsi": "Perawatan ini dirancang untuk mencerahkan dan memperbaiki tekstur kulit, membe" +
                "rikan efek glowing yang sehat dan bercahaya.",
        "harga": "IDR 190k ~ 1.100k",
        "gambar": "/static/image/treatment_2.jpg",
        "rating": "52,912",
        "review": "4,01",
        "discount": "",
        "limited_discount": [
            "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                    "nsaction, syarat dan ketentuan berlaku"
        ],
        "key_highlight": [
            "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
        ],
        "spesification": [
            {
                "nama": "Microdermabrasi",
                "harga": "190k"
            }, {
                "nama": "Oxygen",
                "harga": "210k"
            }, {
                "nama": "Microlightening",
                "harga": "225k"
            }, {
                "nama": "Microlightening + Pdt",
                "harga": "260k"
            }, {
                "nama": "Chemical Peeling",
                "harga": "285k"
            }, {
                "nama": "Micro + Oxy",
                "harga": "290k"
            }, {
                "nama": "Hydrapeel",
                "harga": "300k"
            }, {
                "nama": "Detox + Micro + Ultrasound",
                "harga": "300k"
            }, {
                "nama": "Peeling Diamond",
                "harga": "365k"
            }, {
                "nama": "Hydrapell + Oxy",
                "harga": "380k"
            }, {
                "nama": "Microneedling",
                "harga": "650k"
            }, {
                "nama": "DNA Salmon",
                "harga": "1100k"
            }
        ]
    }, {
        "id": 3,
        "nama": "FACIAL Treatment",
        "deskripsi": "Facial merupakan perawatan dasar untuk membersihkan, melembapkan, dan meremaja" +
                "kan kulit wajah, serta memberikan relaksasi.",
        "harga": "IDR 100k ~ 185k",
        "gambar": "/static/image/treatment_3.jpg",
        "rating": "52,912",
        "review": "4,01",
        "discount": "50",
        "limited_discount": [
            "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                    "nsaction, syarat dan ketentuan berlaku"
        ],
        "key_highlight": [
            "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
        ],
        "spesification": [
            {
                "nama": "Kefir Facial",
                "harga": "100k"
            }, {
                "nama": "Facial + Peel of mask",
                "harga": "110k"
            }, {
                "nama": "Collagen Facial",
                "harga": "155k"
            }, {
                "nama": "Ultrasound Facial",
                "harga": "180k"
            }, {
                "nama": "Detox Facial",
                "harga": "185k"
            }
        ]
    }, {
        "id": 4,
        "nama": "BEKAS JERAWAT Treatment",
        "deskripsi": "Perawatan ini bertujuan untuk mengurangi dan menghilangkan bekas jerawat, meng" +
                "haluskan tekstur kulit, dan meratakan warna kulit.",
        "harga": "IDR 155k ~ 650k",
        "gambar": "/static/image/treatment_4.jpg",
        "rating": "52,912",
        "review": "4,01",
        "discount": "36",
        "limited_discount": [
            "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                    "nsaction, syarat dan ketentuan berlaku"
        ],
        "key_highlight": [
            "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
        ],
        "spesification": [
            {
                "nama": "Photodinamic Therapy",
                "harga": "155k"
            }, {
                "nama": "Microdermabrasi",
                "harga": "190k"
            }, {
                "nama": "Microlightening",
                "harga": "225k"
            }, {
                "nama": "Chemical Peeling",
                "harga": "285k"
            }, {
                "nama": "Microneedling",
                "harga": "650k"
            }
        ]
    }, {
        "id": 5,
        "nama": "ANTI AGING/FLEK Treatment",
        "deskripsi": "Perawatan anti-aging difokuskan untuk mengurangi tanda-tanda penuaan seperti g" +
                "aris halus, keriput, dan flek hitam, serta meningkatkan elastisitas dan kecera" +
                "han kulit.",
        "harga": "IDR 190k ~ 1.100k",
        "gambar": "/static/image/treatment_5.jpg",
        "rating": "52,912",
        "review": "4,01",
        "discount": "36",
        "limited_discount": [
            "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                    "nsaction, syarat dan ketentuan berlaku"
        ],
        "key_highlight": [
            "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
        ],
        "spesification": [
            {
                "nama": "Microdermabrasi",
                "harga": "190k"
            }, {
                "nama": "Microlightening",
                "harga": "225k"
            }, {
                "nama": "Chemical Peeling",
                "harga": "285k"
            }, {
                "nama": "Hydrapeel",
                "harga": "300k"
            }, {
                "nama": "Microneedling",
                "harga": "650k"
            }, {
                "nama": "DNA Salmon",
                "harga": "1100k"
            }
        ]
    }
]

list_products2 = [
    {
    "id": 1,
    "nama": "Photodinamic Therapy",
    "harga": "155k",
    "kategori": [
        "ACNE", "BEKAS JERAWAT"
    ],
    "deskripsi": "Terapi menggunakan cahaya untuk mengaktifkan obat fotosensitif guna menghancurkan sel abnormal atau bakteri pada kulit.",
    "gambar": "/static/kumpulan_foto_treatment/1.png",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 2,
    "nama": "Oxygen",
    "harga": "210k",
    "kategori": [
        "ACNE", "GLOWING/BRIGHTENING"
    ],
    "deskripsi": "Perawatan yang memanfaatkan oksigen murni untuk meningkatkan sirkulasi darah dan memberikan nutrisi ke kulit.",
    "gambar": "/static/kumpulan_foto_treatment/2.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 3,
    "nama": "Chemical Peeling Acne",
    "harga": "285k",
    "kategori": ["ACNE"],
    "deskripsi": "Proses pengelupasan kulit menggunakan bahan kimia untuk mengurangi jerawat dan memperbaiki tekstur kulit.",
    "gambar": "/static/kumpulan_foto_treatment/3.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 4,
    "nama": "Oxy + Pdt ",
    "harga": "240k",
    "kategori": ["ACNE"],
    "deskripsi": "Kombinasi perawatan oksigen dan terapi fotodinamik untuk hasil kulit yang lebih bersih dan sehat.",
    "gambar": "/static/kumpulan_foto_treatment/4.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 5,
    "nama": "Peeling + Pdt ",
    "harga": "320k",
    "kategori": ["ACNE"],
    "deskripsi": "Pengelupasan kimia diikuti dengan terapi fotodinamik untuk memperbaiki masalah kulit seperti jerawat dan penuaan.",
    "gambar": "/static//kumpulan_foto_treatment/5.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 6,
    "nama": "Peeling + Oxy",
    "harga": "385k",
    "kategori": ["ACNE"],
    "deskripsi": "Pengelupasan kimia diikuti dengan terapi oksigen untuk merevitalisasi dan memperbaiki kulit.",
    "gambar": "/static/kumpulan_foto_treatment/6.png",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 7,
    "nama": "Peeling + Pdt + Oxy",
    "harga": "420k",
    "kategori": ["ACNNE"],
    "deskripsi": "Kombinasi pengelupasan kimia, terapi fotodinamik, dan oksigen untuk perawatan kulit yang komprehensif.",
    "gambar": "/static/kumpulan_foto_treatment/7.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 8,
    "nama": "Microdermabrasi",
    "harga": "190k",
    "kategori": [
        "GLOWING/BRIGHTENING", "BEKAS JERAWAT", "ANTI AGING/FLEK"
    ],
    "deskripsi": "Prosedur non-invasif yang menggunakan alat dengan kristal halus untuk mengangkat lapisan kulit mati dan merangsang produksi sel kulit baru.",
    "gambar": "/static/kumpulan_foto_treatment/8.png",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 9,
    "nama": "Microlightening",
    "harga": "225k",
    "kategori": [
        "GLOWING/BRIGHTENING", "BEKAS JERAWAT", "ANTI AGING/FLEK"
    ],
    "deskripsi": "Perawatan pencerah kulit menggunakan teknik mikro untuk mengurangi hiperpigmentasi dan meratakan warna kulit.",
    "gambar": "/static//kumpulan_foto_treatment/9.png",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 10,
    "nama": "Microlightening + Pdt",
    "harga": "260k",
    "kategori": ["GLOWING/BRIGHTENING"],
    "deskripsi": "Kombinasi pencerah kulit mikro dengan terapi fotodinamik untuk hasil pencerahan dan peremajaan kulit.",
    "gambar": "/static/kumpulan_foto_treatment/10.png",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 11,
    "nama": "Chemical Peeling",
    "harga": "285k",
    "kategori": [
        "GLOWING/BRIGHTENING", "BEKAS JERAWAT", "ANTI AGING/FLEK"
    ],
    "deskripsi": "Pengelupasan kulit menggunakan bahan kimia untuk menghilangkan sel kulit mati dan meningkatkan regenerasi sel kulit baru.",
    "gambar": "/static/kumpulan_foto_treatment/11.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 12,
    "nama": "Micro + Oxy",
    "harga": "290k",
    "kategori": ["GLOWING/BRIGHTENING"],
    "deskripsi": "Kombinasi mikrodermabrasi dengan terapi oksigen untuk kulit yang lebih halus dan bernutrisi",
    "gambar": "/static/kumpulan_foto_treatment/12.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 13,
    "nama": "Hydrapeel",
    "harga": "300k",
    "kategori": [
        "GLOWING/BRIGHTENING", "ANTI AGING/FLEK"
    ],
    "deskripsi": "Prosedur pengelupasan kulit yang menggunakan teknik hidrasi untuk membersihkan pori-pori dan memperbaiki tekstur kulit.",
    "gambar": "/static/kumpulan_foto_treatment/13.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 14,
    "nama": "Detox + Micro + Ultrasound",
    "harga": "300k",
    "kategori": ["GLOWING/BRIGHTENING"],
    "deskripsi": "Kombinasi perawatan detoksifikasi, mikrodermabrasi, dan ultrasound untuk membersihkan, meremajakan, dan memperbaiki kulit.",
    "gambar": "/static/kumpulan_foto_treatment/14.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 15,
    "nama": "Peeling Diamond",
    "harga": "365k",
    "kategori": ["GLOWING/BRIGHTENING"],
    "deskripsi": "Pengelupasan kulit menggunakan alat berlian untuk hasil pengelupasan yang lebih halus dan efektif.",
    "gambar": "/static/kumpulan_foto_treatment/15.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 16,
    "nama": "Hydrapell + Oxy",
    "harga": "380k",
    "kategori": ["GLOWING/BRIGHTENING"],
    "deskripsi": "Kombinasi hydrapeel dengan terapi oksigen untuk membersihkan dan menutrisi kulit secara mendalam.",
    "gambar": "/static/kumpulan_foto_treatment/16.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 17,
    "nama": "Microneedling",
    "harga": "650k",
    "kategori": [
        "GLOWING/BRIGHTENING", "BEKAS JERAWAT", "ANTI AGING/FLEK"
    ],
    "deskripsi": "Prosedur menggunakan jarum kecil untuk merangsang produksi kolagen dan elastin, memperbaiki tekstur dan tampilan kulit.",
    "gambar": "/static/kumpulan_foto_treatment/17.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 18,
    "nama": "DNA Salmon",
    "harga": "1100k",
    "kategori": [
        "GLOWING/BRIGHTENING", "ANTI AGING/FLEK"
    ],
    "deskripsi": "Perawatan menggunakan ekstrak DNA ikan salmon untuk meremajakan kulit dan meningkatkan regenerasi sel kulit.",
    "gambar": "/static/kumpulan_foto_treatment/18.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 19,
    "nama": "Kefir Facial",
    "harga": "100k",
    "kategori": ["FACIAL"],
    "deskripsi": "Perawatan wajah menggunakan kefir untuk memberikan nutrisi, hidrasi, dan meningkatkan kesehatan kulit.",
    "gambar": "/static/kumpulan_foto_treatment/19.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 20,
    "nama": "Facial + Peel of mask",
    "harga": "110k",
    "kategori": ["FACIAL"],
    "deskripsi": "Perawatan wajah yang diakhiri dengan masker peel-off untuk membersihkan dan menenangkan kulit.",
    "gambar": "/static/kumpulan_foto_treatment/20.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 21,
    "nama": "Collagen Facial",
    "harga": "155k",
    "kategori": ["FACIAL"],
    "deskripsi": "Perawatan wajah yang difokuskan pada penambahan kolagen untuk mengencangkan dan meremajakan kulit.",
    "gambar": "/static/kumpulan_foto_treatment/21.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 22,
    "nama": "Ultrasound Facial",
    "harga": "180k",
    "kategori": ["FACIAL"],
    "deskripsi": "Perawatan wajah menggunakan gelombang ultrasound untuk meningkatkan sirkulasi darah dan penyerapan nutrisi.",
    "gambar": "/static/kumpulan_foto_treatment/22.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 23,
    "nama": "Detox Facial",
    "harga": "185k",
    "kategori": ["FACIAL"],
    "deskripsi": "Perawatan wajah yang bertujuan untuk mengeluarkan racun dan kotoran dari kulit, memberikan hasil yang segar dan bersih.",
    "gambar": "/static/kumpulan_foto_treatment/23.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}, {
    "id": 24,
    "nama": "Microdermabrasi",
    "harga": "190k",
    "kategori": [
        "BEKAS JERAWAT", "ANTI AGING/FLEK"
    ],
    "deskripsi": "Prosedur non-invasif yang menggunakan alat dengan kristal halus untuk mengangkat lapisan kulit mati dan merangsang produksi sel kulit baru.",
    "gambar": "/static/kumpulan_foto_treatment/24.jpg",
    "rating": "52,912",
    "review": "4,01",
    "discount": "36",
    "limited_discount": [
        "discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank", "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time tra" +
                "nsaction, syarat dan ketentuan berlaku"
    ],
    "key_highlight": [
        "Menggunakan Teknologi Terkini", "tanpa menggunakan bahan kimia terlarang", "ruangan nyaman dan ber AC", "Testimoni banyak", "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"
    ],
    "spesification": ""
}
]
project_directory = os.path.abspath(os.path.dirname(__file__))
upload_folder = os.path.join(project_directory, 'static', 'upload')
app.config['UPLOAD_FOLDER'] = upload_folder
app.config['SECRET_KEY'] = 'bukan rahasia'
@app.route("/home")
def home_view(): return render_template("index.html")
@app.route("/")
def home(): return render_template("skin_detection.html")
# return render_template("index.html")
@app.route("/bot")
def chatbot(): return render_template("chatbot.html")
@app.route("/products")
def products(): return render_template(
    "products.html",
    list_products = list_products
)
@app.route("/products_detail/<int:id>")
def products_detail(id): 
    product = next((product for product in list_products if product["id"] == id) ,None) 
    if product : 
        print(product)
        return render_template("product_detail.html", product = product)
    else : 
        print("Product not found")
    return jsonify({"error": "Product not found"}), 404 @app.route("/skin_detection")
def skin_detection() : 
    return redirect(url_for('home'))
# return render_template("skin_detection.html")
@app.route("/get")
def get_bot_response() : 
    user_input = str(request.args.get('msg'))
    print(user_input)
    result = generate_response(user_input)
    return result @app.route("/get/berminyak")
def get_bot_response_berminyak() : 
    jenis_kulit = "berminyak" 
    print(jenis_kulit)
    user_input = str(request.args.get('msg'))
    print(user_input)
    result = generate_response(user_input)
    result = str(result)
    return result @app.route("/get/kering")
def get_bot_response_kering() : 
    jenis_kulit = "kering" 
    print(jenis_kulit)
    user_input = str(request.args.get('msg'))
    print(user_input)
    result = generate_response(user_input)
    result = str(result)
    return result @app.route("/get/normal")
def get_bot_response_normal() : 
    jenis_kulit = "normal" 
    print(jenis_kulit)
    user_input = str(request.args.get('msg'))
    print(user_input)
    result = generate_response(user_input)
    result = str(result)
    return result @app.route("/skin_detection")
def skin_detect() : 
    return render_template("skin_detection.html")
@app.route("/skin_detection_submit", methods = ["POST"])
def skin_detection_submit() : 
    file = request.files['gambar'] 
    try : 
        img = Image.open(file)
        if img.mode == 'RGBA' : 
            img = img.convert('RGB')
            random_name = uuid.uuid4().hex + ".jpg" 
            destination = os.path.join(app.config['UPLOAD_FOLDER'], random_name)
            img.save(destination)
            hasil = predict_skin(destination)
            print(hasil)
            if hasil == False : 
                if session['jenis_kulit'] : 
                    session.pop('jenis_kulit')
                    return jsonify({"msg": "Gagal, Tidak Terdeteksi Wajah"})
                session['jenis_kulit'] = hasil 
                return jsonify({"msg": "SUKSES", "hasil": hasil, "img": random_name})
    except Exception as e : 
        print(str(e))
        return jsonify({"error": str(e)})
        
if __name__ == "__main__" : app.run(debug = True)