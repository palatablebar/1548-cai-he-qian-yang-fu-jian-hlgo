from collections.abc import Mapping
from decimal import Decimal

from .contracts import MeasureIssue


from dataclasses import dataclass


def form_number(form, sheet, name, minimum, maximum):
    from .service import number

    table = form.get(sheet)
    if not isinstance(table, Mapping):
        raise MeasureIssue(sheet, 'FORM_SECTION_REQUIRED')
    return Decimal(str(number(table.get(name), name, minimum, maximum)))


@dataclass(frozen=True, slots=True)
class PrintTicketsSheet:
    cyan_milli_od: Decimal
    magenta_milli_od: Decimal
    plate_nm: Decimal
    paper_basis_points: Decimal
    ink_deci_c: Decimal
    image_work_blocks: Decimal

    def fields(self):
        return {
            'cyan_shift': float(self.cyan_milli_od) / 10,
            'magenta_shift': float(self.magenta_milli_od) / 10,
            'register_um': float(self.plate_nm) / 1000,
            'moisture': float(self.paper_basis_points) / 10,
            'ink_c': float(self.ink_deci_c) / 10,
            'image_blocks': float(self.image_work_blocks),
        }

    def validation(self):
        fields = self.fields()
        cyan_shift = fields['cyan_shift']
        magenta_shift = fields['magenta_shift']
        register_um = fields['register_um']
        moisture = fields['moisture']
        ink_c = fields['ink_c']
        image_blocks = fields['image_blocks']
        amount_of_color = abs(cyan_shift)+abs(magenta_shift)
        optical_radius = (cyan_shift**2+magenta_shift**2)**.5
        register_um_per_bar = register_um/max(1,image_blocks)
        dry_paper = moisture<50 and ink_c>37
        alerts = []
        if register_um_per_bar>115:
            alerts.append(('plate_nm', 'RECHECK_PLATE_MEASUREMENT'))
        if dry_paper and optical_radius>49:
            alerts.append(('paper_basis_points', 'DRY_SHEET_INK_MISMATCH'))
        if amount_of_color>82:
            alerts.append(('magenta_milli_od', 'VERIFY_COLOR_UNIT'))
        return tuple(alerts)


def read_print_tickets(form):
    return PrintTicketsSheet(
        cyan_milli_od=form_number(form, '机台密度', 'cyan_milli_od', -240, 430),
        magenta_milli_od=form_number(form, '机台密度', 'magenta_milli_od', -300, 480),
        plate_nm=form_number(form, '套准读数', 'plate_nm', 8000, 128000),
        paper_basis_points=form_number(form, '套准读数', 'paper_basis_points', 400, 950),
        ink_deci_c=form_number(form, '纸张墨路', 'ink_deci_c', 160, 430),
        image_work_blocks=form_number(form, '纸张墨路', 'image_work_blocks', 1, 32),
    )


def explicit_rows(form):
    if not isinstance(form, Mapping):
        raise MeasureIssue('form', 'FORM_OBJECT_REQUIRED')
    note = read_print_tickets(form)
    return note.fields(), note.validation()


def check_native_history(source):
    if not isinstance(source, Mapping) or 'form' not in source:
        return source
    if any(key in source for key in ('cyan_shift', 'magenta_shift', 'register_um', 'moisture', 'ink_c', 'image_blocks')):
        raise MeasureIssue('form','MIXED_FORM_AND_FLAT_READING')
    converted, flags = explicit_rows(source['form'])
    if flags:
        raise MeasureIssue(*flags[0])
    return {**source, **converted}
