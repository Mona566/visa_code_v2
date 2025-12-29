"""
Irish Visa Application Form Auto-Filler
主入口文件 - 从 insert_function 模块导入所有功能
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

# 从模块导入所有功能
from insert_function.utils import (
    OPERATION_DELAY, POSTBACK_DELAY, POSTBACK_WAIT_DELAY, POSTBACK_BETWEEN_DELAY,
    setup_logging, log_operation, logger, verify_page_state, safe_postback_operation
)
from insert_function.page_detection import (
    check_and_handle_error_page, check_application_error, check_homepage_redirect,
    check_page_redirect_after_field_fill, detect_current_page_state,
    detect_page_number_no_refresh, handle_intermediate_page, restart_from_homepage,
    click_next_button
)
from insert_function.form_helpers import (
    fill_dropdown_by_label, select_radio_by_label,
    fill_text_by_label, fill_date_by_label
)
from insert_function.application_management import (
    save_page_source_for_debugging, save_application_number,
    get_saved_application_number, extract_application_number, retrieve_application
)
from insert_function.page_fillers import (
    fill_page_1, fill_page_2, fill_page_3, fill_page_4, fill_page_5,
    fill_page_6, fill_page_7, fill_page_8, fill_page_9, fill_page_10
)
from insert_function.main_flow import (
    auto_fill_inis_form, fill_application_form
)

# 初始化日志
logger = setup_logging()

if __name__ == "__main__":
    # 调用自动填写表单函数
    auto_fill_inis_form()
