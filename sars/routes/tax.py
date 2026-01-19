from flask import Blueprint, request, jsonify

tax_bp = Blueprint("tax", __name__)

def compute_tax_from_payload(payload: dict) -> dict:
    # accept multiple field names for compatibility with frontend
    ctc_annual = float(payload.get("ctc_annual", payload.get("ctc", 0)) or 0)
    travel_allowance_annual = float(
        payload.get("travel_allowance_annual", payload.get("travel_allowance", 0)) or 0
    )
    pension_perc = float(payload.get("pension_perc", 0.075) or 0.075)
    num_dependants = int(payload.get("num_dependants", payload.get("dependants", 1)) or 1)

    # defensive: convert percent like 7.5 -> 0.075
    if pension_perc > 1:
        pension_perc = pension_perc / 100.0

    # Constants (match Next.js implementation)
    PRIMARY_REBATE = 17235
    UIF_CAP_SALARY = 17712 * 12
    MED_CREDIT_MAIN = 364 * 12
    MED_CREDIT_DEP1 = 364 * 12
    MED_CREDIT_ADDITIONAL = 246 * 12

    # Pension contribution capped at R350k
    pension_contribution = min(ctc_annual * pension_perc, 350000)

    # Travel allowance: 80% taxable, 20% non-taxable
    taxable_travel = travel_allowance_annual * 0.8
    non_taxable_travel = travel_allowance_annual * 0.2

    # Taxable income
    taxable_income = max(0.0, ctc_annual - pension_contribution - non_taxable_travel)

    # Tax brackets
    def get_raw_tax(income: float) -> float:
        if income <= 237100:
            return income * 0.18
        elif income <= 370500:
            return 42678 + (income - 237100) * 0.26
        elif income <= 512800:
            return 77362 + (income - 370500) * 0.31
        elif income <= 673000:
            return 121475 + (income - 512800) * 0.36
        elif income <= 857900:
            return 179147 + (income - 673000) * 0.39
        elif income <= 1817000:
            return 251258 + (income - 857900) * 0.41
        else:
            return 644489 + (income - 1817000) * 0.45

    annual_tax_before_rebates = get_raw_tax(taxable_income)

    # Medical credits
    medical_credits = MED_CREDIT_MAIN
    if num_dependants >= 1:
        medical_credits += MED_CREDIT_DEP1
    if num_dependants > 1:
        medical_credits += (num_dependants - 1) * MED_CREDIT_ADDITIONAL

    final_annual_tax = max(0.0, annual_tax_before_rebates - PRIMARY_REBATE - medical_credits)

    # UIF (1% capped)
    uif_annual = min(ctc_annual, UIF_CAP_SALARY) * 0.01

    # Monthly breakdown
    monthly_gross = ctc_annual / 12.0
    monthly_paye = final_annual_tax / 12.0
    monthly_pension = pension_contribution / 12.0
    monthly_uif = uif_annual / 12.0
    monthly_net_pay = monthly_gross - monthly_paye - monthly_pension - monthly_uif

    def round2(v: float) -> float:
        return round(v * 100) / 100.0

    result = {
        "monthly_gross": round2(monthly_gross),
        "monthly_paye": round2(monthly_paye),
        "monthly_pension": round2(monthly_pension),
        "monthly_uif": round2(monthly_uif),
        "monthly_net_pay": round2(monthly_net_pay),
    }

    return result

@tax_bp.route("/calculate-tax", methods=["POST"])
def calculate_tax():
    try:
        payload = request.get_json() or {}
        result = compute_tax_from_payload(payload)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Calculation failed", "detail": str(e)}), 400

@tax_bp.route("/calculate", methods=["POST", "OPTIONS", "GET"])
def calculate_tax_api():
    # Respond to preflight / health checks quickly
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    if request.method == "GET":
        return jsonify({"message": "POST JSON { income } to calculate tax"}), 200

    try:
        payload = request.get_json() or {}
        # frontend sample sends { income } — map that to ctc_annual if not provided
        if "income" in payload and "ctc_annual" not in payload and "ctc" not in payload:
            payload["ctc_annual"] = payload.get("income")
        result = compute_tax_from_payload(payload)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Calculation failed", "detail": str(e)}), 400