import logging
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from settings import settings
from auth.auth import get_password_hash
from user.model import DBUser, UserType
from sqlalchemy.ext.asyncio import AsyncSession
from db.engine import get_db
from lpr.model import SettingType
from lpr.crud import BuildingOperation, CameraOperation, GateOperation, LprOperation, SettingOperation, LprSettingOperation
from lpr.schema import BuildingCreate, CameraCreate, CameraSettingCreate, GateCreate, LprCreate, LprSettingCreate

logger = logging.getLogger(__name__)

default_buildings = [
    {
      "name": "central",
      "latitude": "98.0.0",
      "longitude": "98.0.0",
      "description": "شعبه مرکزی"
    },
    {
      "name": "amol",
      "latitude": "98.0.1",
      "longitude": "98.0.1",
      "description": "شعبه آمل"
    }
]
default_gates = [
    {
      "name": "گیت اصلی ساختمان مرکزی",
      "description": "گیت اصلی شعبه مرکزی تهران",
      "gate_type": 2,
      "building_id": 1
    },
    {
      "name": "گیت ورودی",
      "description": "گیت ورودی شعبه مرکزی",
      "gate_type": 0,
      "building_id": 1
    },
    {
      "name": "گیت خروجی",
      "description": "گیت خروجی سازمان مرکزی",
      "gate_type": 1,
      "building_id": 1
    },
    {
      "name": "گیت ورودی/خروجی شعبه",
      "description": "گیت اصلی شعبه آمل",
      "gate_type": 2,
      "building_id": 2
    }
]

default_lpr_settings = [
    {"name": "deep_plate_width_1", "description": "عرض تشخیص پلاک اول", "value": "640", "setting_type": SettingType.INT},
    {"name": "deep_plate_width_2", "description": "عرض تشخیص پلاک دوم", "value": "640", "setting_type": SettingType.INT},
    {"name": "deep_plate_height", "description": "ارتفاع تشخیص پلاک", "value": "480", "setting_type": SettingType.INT},
    {"name": "deep_width", "description": "عرض تصویر تشخیص پلاک", "value": "1280", "setting_type": SettingType.INT},
    {"name": "deep_height", "description": "ارتفاع تصویر تشخیص پلاک", "value": "736", "setting_type": SettingType.INT},
    {"name": "deep_detect_prob", "description": "احتمال تشخیص پلاک", "value": "0.55", "setting_type": SettingType.FLOAT},
    {"name": "combine_plates", "description": "ترکیب پلاک‌های تشخیص داده شده", "value": "1", "setting_type": SettingType.INT},
    {"name": "max_IOU", "description": "بیشترین ترکیب تلاقی", "value": "0.95", "setting_type": SettingType.FLOAT},
    {"name": "min_IOU", "description": "کمترین ترکیب تلاقی", "value": "0.85", "setting_type": SettingType.FLOAT},
    {"name": "nation_alpr", "description": "تشخیص پلاک ملی", "value": "0", "setting_type": SettingType.INT},
    {"name": "ocr_file", "description": "فایل OCR", "value": "ocr_int_model_1.xml", "setting_type": SettingType.STRING},
    {"name": "plate_detection_file", "description": "فایل تشخیص پلاک", "value": "plate_model.xml", "setting_type": SettingType.STRING},
    {"name": "car_file", "description": "فایل تشخیص خودرو", "value": "car_model.xml", "setting_type": SettingType.STRING},
    {"name": "ocr_prob", "description": "احتمال انتخاب OCR", "value": "0.65", "setting_type": SettingType.FLOAT},
    {"name": "plate_width", "description": "حداقل عرض پلاک", "value": "30", "setting_type": SettingType.INT},
    {"name": "plate_height", "description": "حداقل ارتفاع پلاک", "value": "10", "setting_type": SettingType.INT},
    {"name": "num_frame_process", "description": "تعداد فریم‌های پردازش", "value": "1", "setting_type": SettingType.INT},
    {"name": "num_send_frame", "description": "تعداد فریم‌های ارسال شده", "value": "1", "setting_type": SettingType.INT},
    {"name": "live_scale", "description": "مقیاس زنده", "value": "1", "setting_type": SettingType.INT},
    {"name": "recive_plate_status", "description": "دریافت وضعیت پلاک", "value": "0", "setting_type": SettingType.INT},
    {"name": "relay_ip", "description": "آی‌پی رله", "value": "192.168.1.91", "setting_type": SettingType.STRING},
    {"name": "relay_port", "description": "پورت رله", "value": "2000", "setting_type": SettingType.INT},
    {"name": "video", "description": "حالت ویدئو", "value": "0", "setting_type": SettingType.INT},
    {"name": "debug", "description": "حالت اشکال‌زدایی", "value": "0", "setting_type": SettingType.INT},
    {"name": "type_of_link", "description": "نوع پیوند", "value": "video", "setting_type": SettingType.STRING},
    {"name": "show_live", "description": "نمایش زنده", "value": "0", "setting_type": SettingType.INT},
    {"name": "use_cpu", "description": "استفاده از CPU", "value": "0", "setting_type": SettingType.INT},
    {"name": "last_read_send", "description": "آخرین ارسال خواندن", "value": "1", "setting_type": SettingType.INT},
    {"name": "use_cuda", "description": "استفاده از CUDA", "value": "0", "setting_type": SettingType.INT},
    {"name": "TCP_IP", "description": "استفاده از TCP/IP", "value": "1", "setting_type": SettingType.INT},
    {"name": "car_detection", "description": "تشخیص خودرو", "value": "0", "setting_type": SettingType.INT},
    {"name": "car_detection_scale", "description": "مقیاس تشخیص خودرو", "value": "0.2", "setting_type": SettingType.FLOAT},
    {"name": "multi_language", "description": "چند زبانگی", "value": "1", "setting_type": SettingType.INT},
    {"name": "base_api", "description": "آدرس پایه API", "value": "http://lpr.pasasystems.ir/api", "setting_type": SettingType.STRING},
    {"name": "deep_car_width", "description": "عرض تشخیص خودرو", "value": "512", "setting_type": SettingType.INT},
    {"name": "deep_car_height", "description": "ارتفاع تشخیص خودرو", "value": "256", "setting_type": SettingType.INT},
    {"name": "start_car_detect", "description": "شروع تشخیص خودرو", "value": "0.4", "setting_type": SettingType.FLOAT},
    {"name": "change_day_night", "description": "تغییر روز و شب", "value": "1", "setting_type": SettingType.INT},
    {"name": "deep_width_car_plate", "description": "عرض خودرو پلاک", "value": "320", "setting_type": SettingType.INT},
    {"name": "deep_height_car_plate", "description": "ارتفاع خودرو پلاک", "value": "160", "setting_type": SettingType.INT},
    {"name": "deep_width_no_car_plate", "description": "عرض بدون خودرو پلاک", "value": "1280", "setting_type": SettingType.INT},
    {"name": "deep_height_no_car_plate", "description": "ارتفاع بدون خودرو پلاک", "value": "960", "setting_type": SettingType.INT},
    {"name": "base_path", "description": "مسیر پایه", "value": "D:\\home\\linaro\\images", "setting_type": SettingType.STRING},
    {"name": "db_adress", "description": "آدرس پایگاه داده", "value": "D:\\client_firefox\\transist.db", "setting_type": SettingType.STRING},
    {"name": "mysql_user", "description": "نام کاربری MySQL", "value": "root", "setting_type": SettingType.STRING},
    {"name": "mysql_pass", "description": "رمز عبور MySQL", "value": "1234", "setting_type": SettingType.STRING},
    {"name": "database", "description": "نام پایگاه داده", "value": "parking2", "setting_type": SettingType.STRING},
    {"name": "mysql_host", "description": "میزبان MySQL", "value": "localhost", "setting_type": SettingType.STRING},
    {"name": "track_plates", "description": "ردیابی پلاک‌ها", "value": "0", "setting_type": SettingType.INT},
    {"name": "relay_key", "description": "کلید رله", "value": "0,1;2,3;-1,-1;4,5", "setting_type": SettingType.STRING}
]

# Function to populate the camera settings table with initial settings
default_camera_settings = [
    {"name": "ViewPointX", "description": "مختصات X نقطه دید", "value": "0", "setting_type": SettingType.INT},
    {"name": "ViewPointY", "description": "مختصات Y نقطه دید", "value": "0", "setting_type": SettingType.INT},
    {"name": "ViewPointWidth", "description": "عرض نقطه دید", "value": "1920", "setting_type": SettingType.INT},
    {"name": "ViewPointHeight", "description": "ارتفاع نقطه دید", "value": "1080", "setting_type": SettingType.INT},
    {"name": "MaxDeviation", "description": "حساسیت تشخیص شیء - انحراف حداکثر", "value": "100", "setting_type": SettingType.INT},
    {"name": "MinDeviation", "description": "حساسیت تشخیص شیء - انحراف حداقل", "value": "5", "setting_type": SettingType.INT},
    {"name": "ObjectSize", "description": "حداقل اندازه شیء برای تشخیص", "value": "250", "setting_type": SettingType.INT},
    {"name": "BufferSize", "description": "اندازه بافر", "value": "10", "setting_type": SettingType.INT},
    {"name": "CameraDelayTime", "description": "زمان تأخیر دوربین", "value": "200", "setting_type": SettingType.INT},
    {"name": "CameraAddress", "description": "آدرس RTSP دوربین", "value": "D:\\programs\\test_video\\+-1_20230920-112542_1_189.avi", "setting_type": SettingType.STRING},
    {"name": "num_frame_process", "description": "تعداد فریم‌های پردازش شده", "value": "1", "setting_type": SettingType.INT},
    {"name": "num_send_frame", "description": "تعداد فریم‌های ارسال شده", "value": "1", "setting_type": SettingType.INT},
    {"name": "live_scale", "description": "ضریب مقیاس زنده", "value": "1", "setting_type": SettingType.INT},
    {"name": "recive_plate_status", "description": "دریافت وضعیت پلاک", "value": "0", "setting_type": SettingType.INT},
    {"name": "relay_ip", "description": "آدرس IP رله", "value": "192.168.1.91", "setting_type": SettingType.STRING},
    {"name": "relay_port", "description": "پورت رله", "value": "2000", "setting_type": SettingType.INT},
    {"name": "type_of_link", "description": "نوع پیوند", "value": "rtsp", "setting_type": SettingType.STRING},
]

default_lprs = [
    {
      "name": "ماژول پلاک خوان۱",
      "description": "پلاک خوان دوربین گیت۱ برای ورودی/خروجی",
      "ip": "185.81.99.23",
      "port": 45,
      "auth_token": "dBzsEzYuBy6wgiGlI4UUXJPLp1OoS0Cc2YgyCFOCh2U7pvH16ucL1334OjCmeWFJ",
      "latitude": "98.0.0",
      "longitude": "98.0.0",
      "gate_id": 1
    },
    {
      "name": "ماژول پلاک خوان۲",
      "description": "پلاک خوان دوربین گیت۱ برای ورودی/خروجی",
      "ip": "185.81.99.23",
      "port": 46,
      "auth_token": "dBzsEzYuBy6wgiGlI4UUXJPLp1OoS0Cc2YgyCFOCh2U7pvH16ucL1334OjCmeWFJ",
      "latitude": "98.0.0",
      "longitude": "98.0.0",
      "gate_id": 1
    },
    {
      "name": "ماژول پلاک خوان۳",
      "description": "پلاک خوان دوربین گیت۱ برای ورودی",
      "ip": "185.81.99.23",
      "port": 47,
      "auth_token": "dBzsEzYuBy6wgiGlI4UUXJPLp1OoS0Cc2YgyCFOCh2U7pvH16ucL1334OjCmeWFJ",
      "latitude": "98.0.0",
      "longitude": "98.0.0",
      "gate_id": 2
    },
    {
      "name": "ماژول پلاک خوان۴",
      "description": "پلاک خوان دوربین گیت۱ برای خروجی",
      "ip": "185.81.99.23",
      "port": 48,
      "auth_token": "dBzsEzYuBy6wgiGlI4UUXJPLp1OoS0Cc2YgyCFOCh2U7pvH16ucL1334OjCmeWFJ",
      "latitude": "98.0.0",
      "longitude": "98.0.0",
      "gate_id": 1
    },
    {
      "name": "ماژول پلاک خوان۵",
      "description": "پلاک خوان دوربین گیت۲ برای ورودی/خروجی",
      "ip": "185.81.99.23",
      "port": 49,
      "auth_token": "dBzsEzYuBy6wgiGlI4UUXJPLp1OoS0Cc2YgyCFOCh2U7pvH16ucL1334OjCmeWFJ",
      "latitude": "98.0.0",
      "longitude": "98.0.0",
      "gate_id": 2
    }
]

default_cameras = [
    {
      "name": "دوربین ۱",
      "latitude": "1.0.1",
      "longitude": "1.0.1",
      "description": "دوربین اصلی گیت",
      "gate_id": 1,
    },
    {
      "name": "دوربین دوم",
      "latitude": "2.0.1",
      "longitude": "2.0.1",
      "description": "دوربین گیت ورود",
      "gate_id": 2,
    },
    {
      "name": "دوربین سوم",
      "latitude": "3.0.1",
      "longitude": "3.0.1",
      "description": "دوربین گیت خروج",
      "gate_id": 3,
    },
    {
      "name": "دوربین گیت اصلی",
      "latitude": "4.0.1",
      "longitude": "4.0.1",
      "description": "دوربین اصلی(ورود/خروج)",
      "gate_id": 4,
    },
]


async def initialize_defaults(db: AsyncSession):
    # Initialize default camera settings
    camera_setting_op = SettingOperation(db)
    for setting in default_camera_settings:
        existing_setting = await camera_setting_op.get_setting_by_name(setting["name"])
        if not existing_setting:
            setting_obj = CameraSettingCreate(
                name=setting["name"],
                description=setting.get("description", ""),
                value=setting["value"],
                setting_type=setting["setting_type"]
            )
            await camera_setting_op.create_setting(setting_obj)
    print("default camera settings created!!!")

    # Initialize default LPR settings
    lpr_setting_op = LprSettingOperation(db)
    for setting in default_lpr_settings:
        existing_setting = await lpr_setting_op.get_setting_by_name(setting["name"])
        if not existing_setting:
            setting_obj = LprSettingCreate(
                name=setting["name"],
                description=setting.get("description", ""),
                value=setting["value"],
                setting_type=setting["setting_type"]
            )
            await lpr_setting_op.create_setting(setting_obj)
    print("default lpr settings created!!!")

    building_op = BuildingOperation(db)
    for building in default_buildings:
        building_obj = BuildingCreate(
            name=building["name"],
            latitude=building["latitude"],
            longitude=building["longitude"],
            description=building["description"]
        )
        await building_op.create_building(building_obj)
    print("default buildings created!!!")

    gate_op = GateOperation(db)
    for gate in default_gates:
        gate_obj = GateCreate(
            name=gate["name"],
            description=gate["description"],
            gate_type=gate["gate_type"],
            building_id=gate["building_id"]
        )
        await gate_op.create_gate(gate_obj)
    print("default gates created!!!")


    lpr_op = LprOperation(db)
    for lpr in default_lprs:
        lpr_obj = LprCreate(
            name=lpr["name"],
            description=lpr["description"],
            latitude=lpr["latitude"],
            longitude=lpr["longitude"],
            ip=lpr["ip"],
            port=lpr["port"],
            auth_token=lpr["auth_token"],
            gate_id=lpr["gate_id"]
        )
        new_lpr = await lpr_op.create_lpr(lpr_obj)
        print(f"Created lpr with ID: {new_lpr.id}")
    print("default lprs created!!!")

    camera_op = CameraOperation(db)
    for camera in default_cameras:
        camera_obj = CameraCreate(
            name=camera["name"],
            description=camera["description"],
            latitude=camera["latitude"],
            longitude=camera["longitude"],
            gate_id=camera["gate_id"]
        )
        try:
            created_camera = await camera_op.create_camera(camera_obj)
            logger.info(f"Created camera: {created_camera.name} with ID: {created_camera.id}")
        except HTTPException as he:
            logger.error(f"Failed to create camera {camera['name']}: {he.detail}")
        except Exception as e:
            logger.error(f"Unexpected error while creating camera {camera['name']}: {e}")
    logger.info("Default cameras created!!!")


async def create_default_admin(session: AsyncSession):
    pass
    logger.info("Checking if default admin user exists")
    result = await session.execute(select(DBUser).filter(DBUser.username == settings.ADMIN_USERNAME))
    admin = result.unique().scalars().first()

    if admin:
        logger.info("Default admin user already exists")
        print("Admin user already exists.")
        return

    try:
        # If no admin exists, create one with secure credentials
        admin_user = DBUser(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            user_type=UserType.ADMIN,
            is_active=True
        )

        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        logger.info("Default admin user created successfully")
        print("Default admin user created successfully.")
        print(f"Admin: {admin_user.username}")


    except SQLAlchemyError as error:
        await session.rollback()
        logger.critical(f"Failed to creat default admin user: {error}")
        raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not create user")
