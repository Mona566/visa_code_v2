import os
import json

from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
from pathlib import Path

llm = ChatOpenAI(model_name=os.environ.get("MODEL"), temperature=0.4)

irish_visa_template_prompt = '''
你是一名爱尔兰签证材料字段识别专家。
请从文本中精确提取以下字段，缺失字段用 null 填写，日期统一为 YYYY-MM-DD，注意可选项的说明：

1. Application Information:
   - visa_type (选项: "Long Stay (D)", "Short Stay (C)", null)   //choose from the list
   - journey_type (选项: "Single", "Multiple", null)            //choose from the list
   - reason_for_travel (选项: "Study", "Tourism", "Work", null) //choose from the list
   - study_visa_type (如: "English Language (ILEP)", null)      //choose from the list
   - ILEP_number_and_title                                     //university offer
   - purpose_of_travel                                         // tourist/study/others

2. Personal Information:
   - surname                                                 //passport or id_card or house registration file
   - forename                                                 //passport or id_card or house registration file
   - other_name                                                 //passport or id_card or house registration file
   - date_of_birth                                                 //passport or id_card or house registration file
   - gender (选项: "Male", "Female", "Other", null)
   - place_of_birth                                                 //passport or id_card or house registration file
   - nationality                                                 //passport or id_card or house registration file
   - current_location                                                 //passport or id_card or house registration file
   - current_address                                                //passport or id_card or house registration file

3. Contact Information:
   - address_line_1                                                //passport or id_card or house registration file
   - address_line_2                                                //passport or id_card or house registration file
   - address_line_3
   - address_line_4
   - phone                                                //extra info
   - email                                                //extra info

4. Passport Information:
   - passport_number                                                //passport
   - passport_type (选项: "National Passport", "Travel Document", null)
   - issuing_authority                                                //passport
   - date_of_issue                                                //passport
   - date_of_expiry                                                //passport
   - first_passport (选项: True, False, null)

5. Employment / Student Status:
   - currently_employed (选项: Yes, No, null)
   - currently_student (选项: Yes, No, null)

6. Travel Companions:
   - travelling_with_others (选项: Yes, No, null)

7. Host / Accommodation in Ireland:
   - host_address_line_1                                                //hotel reservation letter
   - host_address_line_2                                                //hotel reservation letter
   - host_address_line_3
   - host_address_line_4
   - host_phone                                                //hotel reservation letter
   - host_name                                                //hotel reservation letter
   - host_relationship (选项: "Family", "Friend", "Accommodation provider", null)
   - host_email                                                //hotel reservation letter
   - host_occupation                                                //hotel reservation letter

8. Family Information:
   - personal_status (选项: "Single", "Married", "Divorced", "Widowed", null)
   - spouse_details:                                                //extra info
       - surname                                                
       - forenames                                              
       - other_names
       - date_of_birth
       - passport_number
       - gender (选项: "Male", "Female", "Other", null)
       - current_country
       - travelling_with_applicant (Yes/No/null)
   - children_details:                                                 //extra info
       - for each child (最多6个):
           - surname
           - forename
           - date_of_birth
           - gender (选项: "Male", "Female", "Other", null)
           - nationality
           - travelling_with_applicant (Yes/No/null)

9. Education / Qualification:
   - accepted_on_course_in_ireland (Yes/No/null)                                             //offer
   - studied_in_ireland_before (Yes/No/null)
   - speaks_english (Yes/No/null)
   - education_history: list of previous education entries                                    //graduation certificate
       - school_name
       - from_date
       - to_date
       - qualification_obtained
       - major_or_specialization (如适用)

10. Employment History:                                   //employment certificate
    - employer_name
    - from_date
    - to_date
    - position_held

11. Financial Support:
    - self_funded (Yes/No/null)
    - sponsor_count (整数/null)
    - main_sponsor:                                  //sponsorship letter
        - name
        - relationship_to_applicant
        - address_line_1
        - address_line_2
        - address_line_3
        - contact_phone
    - other_funding_sources

12. Agency / Assistance:
    - assisted_by_agent (Yes/No/null)

13. Visa / Immigration History:
    - previous_irish_visa_application (Yes/No/null)
    - previous_irish_visa_issued (Yes/No/null)
    - previous_irish_visa_refused (Yes/No/null)
    - previous_visa_refused_other_countries (Yes/No/null)
    - deportation_notices (Yes/No/null)
    - criminal_convictions (Yes/No/null)

14. Travel Document Details (如有多本护照):
    - passport_1:                                                //passport
        - passport_number
        - issuing_authority
        - date_of_issue
        - date_of_expiry
    - passport_2:                                                //passport
        - passport_number
        - issuing_authority
        - date_of_issue
        - date_of_expiry

15. Travel Details:                                                //offer letter
    - proposed_entry_date
    - proposed_exit_date
    - multi_entry (Yes/No/null)
    - accommodation_address_in_ireland                              //accommodation booking letter

16. Study Details in Ireland:                                                //offer
    - course_name
    - course_level
    - course_start_date
    - course_end_date
    - course_length_weeks
    - study_purpose

17. Emergency Contact:                                                //extra info
    - name
    - relationship
    - phone
    - email
    - contact_address

注意：
- 所有字段必须提取，不要生成解释性文字。
- 缺失字段用 null。
- OCR 换行错误或乱码尽量修复，但不要臆造信息。
- 输出为 JSON 嵌套结构清晰。

请根据以下文本内容提取相应签证字段：

{text}
'''


def extract_visa_fields(markdown_text: str) -> dict:
    """
    从Markdown文本中提取签证字段
    
    Args:
        markdown_text: Markdown格式的文本内容
        
    Returns:
        提取的签证字段字典
    """
    # 构建完整的提示词，将文本内容插入模板
    prompt = irish_visa_template_prompt.format(text=markdown_text)
    
    # 调用LLM进行字段提取
    response = llm.invoke(prompt)
    
    # 获取响应内容
    content = response.content.strip()
    
    # 尝试解析JSON
    try:
        # 如果响应是JSON格式，直接解析
        fields = json.loads(content)
    except json.JSONDecodeError:
        # 如果响应不是纯JSON，尝试提取JSON部分
        # 查找JSON代码块或直接提取JSON
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                fields = json.loads(json_match.group())
            except json.JSONDecodeError:
                # 如果还是失败，返回错误信息
                print(f"[WARN] 无法解析JSON，原始响应: {content[:200]}...")
                # 尝试让LLM修复JSON
                fix_prompt = f"请将以下文本修复为合法的JSON格式，只输出JSON，不要其他解释：\n\n{content}"
                fix_response = llm.invoke(fix_prompt)
                try:
                    fields = json.loads(fix_response.content.strip())
                except json.JSONDecodeError:
                    raise ValueError(f"无法解析LLM返回的JSON格式: {fix_response.content[:200]}")
        else:
            raise ValueError(f"响应中未找到JSON格式: {content[:200]}")
    
    return fields


if __name__ == "__main__":
    md_files = [
        "files/passport.pdf.md",
        "files/id_card.pdf.md",
        "files/cover_letter.pdf.md"
    ]

    for md_path in md_files:
        path = Path(md_path)
        if not path.exists():
            print(f"[WARN] 文件不存在: {md_path}")
            continue

        markdown_text = path.read_text(encoding="utf-8")
        print(f"\n[INFO] 正在处理: {md_path}")

        try:
            fields = extract_visa_fields(markdown_text)
            print("[INFO] 提取的签证字段:")
            print(json.dumps(fields, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"[ERROR] 提取失败: {e}")