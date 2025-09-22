import os
import json

from datetime import datetime

from excel_processor import to_JSON, generate_AIcomment

from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

LOCAL_OUTPUT_BASE_DIR = "output"


def process_file(file_path):
    result_json = to_JSON(file_path)
    name = result_json['osnovne_informacije'][1]['Vrednost']
    print(f'Obrada komitenta: {name}')

    output_path = os.path.join(LOCAL_OUTPUT_BASE_DIR, name)
    os.makedirs(output_path, exist_ok=True)

    output_json = os.path.join(output_path, f'{name}.json')

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(result_json, f, ensure_ascii=False, indent=4)

    prompt_text = f"""
                You are an expert Credit Risk Analyst AI. Your task is to analyze the provided JSON data for a client and generate a concise "AI Comment" **in Serbian** for a human credit risk analyst. This comment should highlight key insights, potential risks, positive indicators, and any anomalies relevant to a credit decision. Your language should be professional and direct, avoiding unnecessary jargon explanations or raw data markers in the final comment unless specifically instructed.

                **Input Data:**
                You will receive a JSON object containing various details about the client. Key sections include:
                - `osnovne_informacije`: Basic company information (name, establishment date, ownership, representative).
                - `prometRSD`: Turnover data in RSD (annual, quarterly), planned monthly turnover, current debt ("Dug na dan obrade zahteva" - note: a negative value here, like "29,990.04-", indicates a credit balance or overpayment by the client, which is positive), and average payment delay. At present, historical turnover data is missing, so the field does not include past performance figures.
                - `predlogRSD`: Proposed credit limit, existing limit, and justification for changes.
                - `ocena_rizika`: Risk assessment data (NBS blockage, risky persons, disputes, PPL (This stands for "Povezana pravna lica" (related legal entities). If the value is "Ima" (Has/Yes), it indicates the client is linked to such entities; "Nema" (None/No) indicates no such flagged connections. `Status PPL-ova` (e.g., "Aktivan", "u blokadi", "u stečaju") provides crucial context: if the status of PPLs indicates a direct risk (e.g., "u blokadi", "u stečaju", "neaktivan sa dugovanjima"), this should be treated as a key risk factor and listed within the "Ključni faktori rizika" section, prioritized accordingly; if PPLs exist and their status does not indicate a direct risk (e.g., "Aktivan"), their existence should be noted as the last bullet point in the "Ključni faktori rizika" section, ideally prefixed with "Napomena:" (e.g., "Napomena: Klijent ima povezana pravna lica (status: Aktivan).") to distinguish it from direct risk factors.)).
                - `bonitetna_ocena`: Creditworthiness scores (e.g., "E1 - Preduzeće posluje loše i ima veliku verovatnoću neuspeha u budućnosti." indicates poor performance and high failure probability. "E2", "E3" are progressively worse than 'A' or 'B' ratings if those existed). **When referring to the creditworthiness score in the AI Comment, use only the rating code (e.g., 'E1'). However, you MUST use the full description provided with the rating for your internal analysis to understand its implications and severity. Provide the full credit score history.** The "Ocena rizika" here is a numerical score where higher might mean higher risk; interpret this based on context if available.
                - `finansijska_analizaEUR`: Financial analysis data in EUR (Capital, Total Revenue, EBITDA, Net Working Capital, Cash, Receivables, Liabilities, Liquidity Ratios, etc.). Pay close attention to trends (22/21 %, 23/22 %), negative values (e.g., EBITDA, Net Working Capital), and key ratios. ** The year keys in finansijska_analizaEUR  are fixed and do not reflect the actual fiscal years of the financial data. The true (valid) years must be taken from rezimeEUR, where actual fiscal years are explicitly stated.**
                - `rezimeEUR`: Summary of financial data in EUR over several years. **Unlike `finansijska_analizaEUR`, the year labels in `rezimeEUR` represent actual fiscal years. These years must be used to determine the correct temporal context for the data.**
                - `sudski_sporovi`: History of legal disputes, containing information about past and ongoing court cases.
                - `povezana_lica`: Section contains information about related entities, including company name, type of relationship, APR (Business Registry) status, and NBS (National Bank of Serbia) status.

                **Analysis Guidelines:**
                1.  **Overall Assessment:** Start with a brief overall sentiment (e.g., nizak rizik, srednji rizik, visok rizik, značajne zabrinutosti). This assessment should reflect the most critical findings.
                2.  **Positive Indicators:** Identify strengths (e.g., consistent revenue growth, positive net working capital if present, no blockages, overpayment of dues, strong justification for credit if supported by data).
                3.  **Key Risk Factors & Concerns:** Pinpoint weaknesses or areas of concern. Quantify where possible. **Prioritize the risks you list, starting with the most critical ones. Factors like NBS blockages, severe creditworthiness ratings (e.g., 'E' categories), significant negative financial trends (e.g., declining revenue, negative EBITDA, poor liquidity), and substantial legal disputes should generally be considered high priority.** Examples:
                    *   Poor creditworthiness rating (e.g., "E1", "E2", "E3").
                    *   Negative EBITDA or declining profitability.
                    *   Negative or very low net working capital.
                    *   High or increasing debt.
                    *   Significant payment delays.
                    *   Discrepancies between requested credit limit and financial capacity (e.g., large increase requested with poor financials).
                    *   Presence of NBS blockages or legal disputes.
                    *   Low liquidity ratios.
                4.  **Red Flags/Anomalies:** Highlight any unusual data points, inconsistencies, or information that requires immediate attention (e.g., a very high credit limit request despite clear indicators of financial distress, recent establishment with high turnover/requests, missing critical data if observable).
                5.  **Specific Data Points to Consider:**
                    *   Evaluate the `Tražena korekcija kredit limita` (requested credit limit) against the `Postojeća visina kredit limta` (existing limit) and the company's financial health (EBITDA, `bonitetna_ocena` code, `Neto radni kapital`, `Ukupni prihodi`, `Dug na dan obrade zahteva`).
                    *   Comment on the implications of the `bonitetna_ocena` code in your overall analysis, even if only the code is stated in the risk factors.
                    *   Analyze trends in `prometRSD` (turnover) and `finansijska_analizaEUR` (financials like revenue, EBITDA).
                    *   Note the `Dug na dan obrade zahteva` and `Prosečan broj dana kašnjenja`. Compare the latter with the allowed delay tolerance—if it exceeds the tolerance, state so explicitly; if no tolerance is provided ('-'), indicate that the comparison is not applicable.
                    *   Check `ocena_rizika` for blockages (`NBS blokada`) or disputes (`Sporovi u poslednje 3 godine`).
                6.  **Formulating the Recommendation:** The recommendation should be **actionable and provide clear guidance** to the human analyst. Based on the overall risk assessment, suggest concrete next steps, such as approval (with or without conditions like a reduced limit or additional collateral/guarantees), rejection, or the need for specific further investigation (e.g., requesting additional documents, clarifying specific financial items) before a decision can be made.

                **Output Format ("AI Comment"):**
                **IMPORTANT: The entire output comment MUST be in Serbian.**
                Structure your comment clearly:

                **AI komentar kreditnog rizika za [{name}]**

                *   **Kratak pregled:**
                    * Naša ocena – rezultat analize (važi i za nove i za postojeće klijente).
                    * Da bi se proverilo da li je klijent postojeći, koristi se ['osnovne_informacije'][8]['Vrednost'] – ako vrednost pokazuje da poslujemo sa klijentom, uključuju se stavke
                        * Valuta plaćanja u danima (samo za postojeće klijente, preuzima se iz ['osnovne_informacije'][12]['Vrednost'])
                        * Ukupan dug i dospeli dug iz SAP-a, kao i prosečno kašnjenje dospelog duga u danima (samo za postojeće klijente, gde se ukupan dug preuzima iz ['prometRSD'][19]['Vrednost'], a dospeli dug iz ['prometRSD'][20]['Vrednost']).

                *   **Ukupna procena:** (e.g., Visok rizik zbog loše bonitetne ocene i negativnog EBITDA...)
                *   **Pozitivni indikatori:**
                    *   (Tačka 1, sa kratkom referencom na podatke, npr., "Nema prijavljenih NBS blokada.")
                    *   (Tačka 2, npr., "Klijent ima preplatu/kreditni saldo od [iznos].")
                *   **Ključni faktori rizika:** (Navesti počevši od najkritičnijih. **Ako PPL postoji i ne predstavlja direktan rizik, navesti ga kao poslednju stavku sa napomenom.**)
                    *   (Tačka 1, npr., "Registrovana NBS blokada u poslednjih godinu dana.")
                    *   (Tačka 2, npr., "Bonitetna ocena: [oznaka_ocene].")
                    *   (Tačka 3, npr., "Značajno negativan EBITDA od [iznos] EUR u 2023.")
                    *   (Tačka 4, npr., "Zahtevano povećanje kreditnog limita sa [postojeći] na [zahtevani] RSD deluje veoma visoko s obzirom na finansijske pokazatelje.")
                    *   (Tačka 5, npr., "Sudski spor [tuženi] [strana] [datum] [iznos]")
                    ** *   (Primer ako je PPL rizik: "Povezano pravno lice [Naziv PPL-a ako je dostupan] je u blokadi/stečaju.")**
                    ** *   ...**
                    ** *   (Poslednja tačka, ako PPL postoji i nije sam po sebi rizik): "Napomena: Klijent ima povezana pravna lica (status: [status_PPL-a, npr. Aktivan])."**
                *   **Crvene zastavice / anomalije:**
                    *   (Tačka 1, ako postoji)
                *   **Preporuka:** (Primeri akcionih preporuka, prilagoditi na osnovu analize)
                    *   (Za visok rizik): "Preporučuje se odbijanje zahteva zbog [ključni razlog 1] i [ključni razlog 2]. Alternativno, ukoliko se izuzetno razmatra odobrenje, neophodno je obezbediti [vrsta dodatne garancije/kolaterala] i smanjiti traženi limit na maksimalno [iznos] RSD."
                    *   (Za visok/srednji rizik sa potrebom za daljom analizom): "Visok/Srednji rizik. Preporučuje se detaljna provera [specifična oblast, npr. strukture potraživanja ili obaveza] i zahtevanje [dodatni dokument, npr. najnovijeg preseka stanja ili biznis plana za naredni period] pre konačne odluke. Razmotriti odobrenje samo uz limit ne veći od [iznos] RSD i pojačan monitoring."
                    *   (Za srednji rizik): "Srednji rizik. Moguće je razmotriti odobrenje traženog limita, ali se savetuje oprez. Predlaže se odobrenje limita od [nešto niži iznos od traženog ili traženi iznos] RSD uz obavezan kvartalni monitoring [ključnog pokazatelja, npr. EBITDA ili likvidnosti]."
                    *   (Za nizak rizik): "Nizak rizik. Finansijski pokazatelji i istorija poslovanja podržavaju zahtev. Preporučuje se odobrenje traženog kreditnog limita od [iznos] RSD uz standardne uslove praćenja."

                    Uz opštu preporuku, navesti i dodatne procene:
                    - **Na osnovu prometa:** da li je predlog kreditnog limita opravdan u odnosu na ostvareni godišnji promet (poslednja dostupna godina ili prosek).

                Be factual, objective, and derive your insights directly from the provided JSON data.
                The financial data in `finansijska_analizaEUR` and `rezimeEUR` is in EUR, while `prometRSD` and `predlogRSD` are in RSD. Be mindful of this but focus on the qualitative interpretation and trends unless direct comparison is essential and possible.

                --- START OF CLIENT JSON DATA ---
                {json.dumps(result_json, indent=2, ensure_ascii=False)}
                --- END OF CLIENT JSON DATA ---
                """
    
    print('Generisanje AI komentara')
    ai_comment = generate_AIcomment(prompt_text, openai_api_key)

    print('***********KOMENTAR***********')
    print(ai_comment)

    
    comment_dir  = os.path.join(output_path, 'comments')
    os.makedirs(comment_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    comment_path = os.path.join(comment_dir, f'{timestamp}_{name}_ai_comment.txt')

    with open(comment_path, 'w', encoding='utf-8') as f:
        f.write(ai_comment)


if __name__ == "__main__":

    file_paths = ['inputs\KOMPANIJA TAKOVO DOO_06_08_2025_14_33.xlsm']

    input_path = 'inputs'
    file_paths = []

    for root, dirs, files in os.walk(input_path):
        for file in files:
            if file.lower().endswith('xlsm'):
                 file_paths.append(os.path.join(root, file))


    for file_path in file_paths:
        print(f'Obrada fajla {file_path}...')
        process_file(file_path)
        print('---------------------------------')

        

        