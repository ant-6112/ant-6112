import sys
import os
import glob
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                             QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QMessageBox, QLabel, QHBoxLayout,
                             QListWidget, QListWidgetItem, QCheckBox, QSplitter, QScrollArea,
                             QLineEdit, QToolButton, QInputDialog, QMenu, QComboBox, QSizePolicy)  # Added QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon

from core_logic import (TemplateDefinition, FieldExtractionDefinition, PDFProcessor,
                        load_templates, save_templates,
                        DocumentRunReport, ExtractedFieldResult,
                        save_document_run_report, load_document_run_reports)
from ui_components import (FieldExtractionDialog, ReportViewerDialog, PDFViewerWidget,
                           TemplateConfigurationTab,
                           DARK_BLUE_GRAY, LIGHT_GRAY_BLUE, HSBC_RED, TEAL, MEDIUM_BLUE,
                           ICON_ADD, ICON_EDIT, ICON_DELETE, ICON_UPLOAD, ICON_PREV, ICON_NEXT)

STYLESHEET = f"""
    QMainWindow, QDialog {{ background-color: {LIGHT_GRAY_BLUE}; }}
    QTabWidget::pane {{ border: 1px solid {DARK_BLUE_GRAY}; background-color: white; }}
    QTabBar::tab {{ background: {LIGHT_GRAY_BLUE}; color: {DARK_BLUE_GRAY}; padding: 10px; border: 1px solid {DARK_BLUE_GRAY}; border-bottom: none; }}
    QTabBar::tab:selected {{ background: white; color: {DARK_BLUE_GRAY}; font-weight: bold; }}
    QTabBar::tab:hover {{ background: {MEDIUM_BLUE}; color: white; }}
    QPushButton {{ background-color: {MEDIUM_BLUE}; color: white; padding: 8px 15px; border: 1px solid {DARK_BLUE_GRAY}; border-radius: 4px; font-size: 10pt; }}
    QPushButton:hover {{ background-color: {TEAL}; }}
    QPushButton:pressed {{ background-color: {DARK_BLUE_GRAY}; }}
    QTableWidget {{ gridline-color: {LIGHT_GRAY_BLUE}; font-size: 9pt; }}
    QHeaderView::section {{ background-color: {DARK_BLUE_GRAY}; color: white; padding: 4px; border: 1px solid {LIGHT_GRAY_BLUE}; font-size: 10pt; font-weight: bold; }}
    QLineEdit, QTextEdit, QSpinBox, QComboBox, QDoubleSpinBox {{ padding: 5px; border: 1px solid {DARK_BLUE_GRAY}; border-radius: 3px; background-color: white; }}
    QLabel {{ font-size: 10pt; }}
    QGroupBox {{ font-weight: bold; color: {DARK_BLUE_GRAY}; border: 1px solid {DARK_BLUE_GRAY}; border-radius: 5px; margin-top: 10px; }}
    QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px 0 5px; background-color: {LIGHT_GRAY_BLUE}; }}
    QCheckBox::indicator {{ width: 15px; height: 15px; }}
    QToolButton {{ background-color: transparent; border: none; padding: 2px; qproperty-iconSize: 20px 20px; }}
    QToolButton:hover {{ background-color: {LIGHT_GRAY_BLUE.replace('#', '#A0')}; }}
    QToolButton:pressed {{ background-color: {MEDIUM_BLUE.replace('#', '#A0')}; }}
"""


class RunnerTab(QWidget):
    templates_list_updated = pyqtSignal(list)

    def __init__(self, parent_main_window, parent=None):
        super().__init__(parent)
        self.parent_main_window = parent_main_window
        self.current_folder_path = ""
        self.pdf_files = []
        self.available_templates: list[TemplateDefinition] = []
        self._init_ui()
        self.parent_main_window.templates_updated_signal.connect(self.update_templates_dropdown)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20);
        layout.setSpacing(15)
        template_select_layout = QHBoxLayout()
        template_select_layout.addWidget(QLabel("<b>Select Template to Run:</b>"))
        self.template_combo = QComboBox()
        self.template_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        template_select_layout.addWidget(self.template_combo, 1)
        layout.addLayout(template_select_layout)

        folder_select_layout = QHBoxLayout()
        self.folder_path_label = QLabel("<i>No folder selected.</i>")
        self.folder_path_label.setStyleSheet("color: #555;")
        select_folder_button = QPushButton("Select PDF Folder")
        select_folder_button.setIcon(
            QIcon(self.style().standardIcon(getattr(self.style(), ICON_UPLOAD, self.style().SP_DialogOpenButton))))
        select_folder_button.clicked.connect(self.select_folder)
        folder_select_layout.addWidget(QLabel("Target Folder:"))
        folder_select_layout.addWidget(self.folder_path_label, 1)
        folder_select_layout.addWidget(select_folder_button)
        layout.addLayout(folder_select_layout)

        self.pdf_list_widget = QListWidget()
        self.pdf_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(QLabel("<b>PDF Files Found (check to process):</b>"))
        layout.addWidget(self.pdf_list_widget, 1)

        run_buttons_layout = QHBoxLayout()
        self.run_button = QPushButton("Run Selected Template on Checked PDFs")
        self.run_button.setStyleSheet(f"background-color: {TEAL}; font-weight: bold;")
        self.run_button.setFixedHeight(40)
        self.run_button.clicked.connect(self.run_template_on_pdfs)
        run_buttons_layout.addStretch();
        run_buttons_layout.addWidget(self.run_button);
        run_buttons_layout.addStretch()
        layout.addLayout(run_buttons_layout)

    def update_templates_dropdown(self, templates: list[TemplateDefinition]):
        self.available_templates = templates
        current_selection_id = self.template_combo.currentData()

        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        if not templates:
            self.template_combo.addItem("No templates defined", None)
            self.template_combo.setEnabled(False)
        else:
            for template in templates:
                self.template_combo.addItem(f"{template.name} (ID: {template.template_id})", template.template_id)
            self.template_combo.setEnabled(True)

            if current_selection_id:
                index = self.template_combo.findData(current_selection_id)
                if index != -1:
                    self.template_combo.setCurrentIndex(index)
                elif self.template_combo.count() > 0:
                    self.template_combo.setCurrentIndex(0)
            elif self.template_combo.count() > 0:
                self.template_combo.setCurrentIndex(0)
        self.template_combo.blockSignals(False)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder Containing PDFs")
        if folder_path:
            self.current_folder_path = folder_path
            self.folder_path_label.setText(f"<i>{folder_path}</i>")
            self.pdf_list_widget.clear();
            self.pdf_files = []
            pdf_pattern = os.path.join(folder_path, "*.pdf")
            found_files = glob.glob(pdf_pattern)
            if not found_files:
                self.pdf_list_widget.addItem("No PDF files found in this folder.")
                return

            for fp in found_files:
                self.pdf_files.append(fp)
                item = QListWidgetItem(os.path.basename(fp))
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable);
                item.setCheckState(Qt.Unchecked)
                self.pdf_list_widget.addItem(item)

    def get_checked_pdf_paths(self):
        paths = []
        for i in range(self.pdf_list_widget.count()):
            item = self.pdf_list_widget.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                if item.checkState() == Qt.Checked:
                    full_path = next((fp for fp in self.pdf_files if os.path.basename(fp) == item.text()), None)
                    if full_path: paths.append(full_path)
        return paths

    def run_template_on_pdfs(self):
        selected_template_id = self.template_combo.currentData()
        if not selected_template_id:
            QMessageBox.warning(self, "Run Error", "Please select a template to run.");
            return

        template_to_run = next((t for t in self.available_templates if t.template_id == selected_template_id), None)
        if not template_to_run:
            QMessageBox.critical(self, "Run Error", "Selected template not found (this should not happen).");
            return

        checked_pdf_paths = self.get_checked_pdf_paths()
        if not checked_pdf_paths:
            QMessageBox.warning(self, "Run Error", "No PDF files checked to run on.");
            return

        pdf_processor = PDFProcessor()
        num_reports_generated = 0
        self.parent_main_window.statusBar().showMessage(
            f"Running template '{template_to_run.name}' on {len(checked_pdf_paths)} PDFs...")
        QApplication.processEvents()

        for i, pdf_path in enumerate(checked_pdf_paths):
            self.parent_main_window.statusBar().showMessage(
                f"Processing ({i + 1}/{len(checked_pdf_paths)}): {os.path.basename(pdf_path)}...")
            QApplication.processEvents()

            pdf_processor.load_pdf(pdf_path)
            if not pdf_processor.doc:
                print(f"Skipping {pdf_path}, could not open.")
                doc_report = DocumentRunReport(source_pdf_path=pdf_path,
                                               applied_template_id=template_to_run.template_id)
                err_res = ExtractedFieldResult(template_to_run.template_id, "LOAD_ERROR", "File Load Error",
                                               f"Could not open/process PDF.", pdf_path, -1)
                doc_report.add_field_result(err_res)
                save_document_run_report(doc_report)
                num_reports_generated += 1
                continue

            doc_report = DocumentRunReport(source_pdf_path=pdf_path, applied_template_id=template_to_run.template_id)
            num_pages = pdf_processor.get_page_count()

            pages_to_process = range(num_pages)

            for page_idx in pages_to_process:
                for field_def in template_to_run.field_definitions:
                    extracted_result = pdf_processor.extract_field_data(field_def, page_idx)
                    extracted_result.template_id = template_to_run.template_id
                    doc_report.add_field_result(extracted_result)

            save_document_run_report(doc_report)
            num_reports_generated += 1
            pdf_processor.close()

        final_msg = (f"Processed {len(checked_pdf_paths)} PDF(s) with template '{template_to_run.name}'.\n"
                     f"{num_reports_generated} document report(s) saved.")
        QMessageBox.information(self, "Run Complete", final_msg)
        self.parent_main_window.statusBar().showMessage(final_msg)
        self.parent_main_window.refresh_report_summary_tab()


class RunReportSummaryTab(QWidget):
    def __init__(self, main_app_ref, parent=None):
        super().__init__(parent)
        self.main_app_ref = main_app_ref
        self.run_reports: list[DocumentRunReport] = []
        self._init_ui()
        self.load_and_display_doc_reports()

    def _init_ui(self):
        layout = QVBoxLayout(self);
        layout.setContentsMargins(20, 20, 20, 20);
        layout.setSpacing(15)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("<b>Extraction Reports:</b>"))
        top_layout.addStretch()
        refresh_button = QPushButton("Refresh Report List");
        refresh_button.clicked.connect(self.load_and_display_doc_reports)
        top_layout.addWidget(refresh_button)
        layout.addLayout(top_layout)

        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(4)
        self.reports_table.setHorizontalHeaderLabels(
            ["Processed PDF", "Template Used", "Timestamp", "Fields Extracted"])
        self.reports_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.reports_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.reports_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.reports_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.reports_table.setSelectionBehavior(QAbstractItemView.SelectRows);
        self.reports_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.reports_table.setSelectionMode(QAbstractItemView.SingleSelection);
        self.reports_table.doubleClicked.connect(self.view_selected_doc_report)
        layout.addWidget(self.reports_table, 1)

        view_button = QPushButton("View Selected Report Details");
        view_button.clicked.connect(self.view_selected_doc_report)
        view_button_layout = QHBoxLayout();
        view_button_layout.addStretch();
        view_button_layout.addWidget(view_button)
        layout.addLayout(view_button_layout)

    def load_and_display_doc_reports(self):
        self.run_reports = load_document_run_reports()
        self.reports_table.setRowCount(0)
        for report in self.run_reports:
            row = self.reports_table.rowCount();
            self.reports_table.insertRow(row)
            self.reports_table.setItem(row, 0, QTableWidgetItem(report.source_pdf_path or "N/A"))

            template_name = "N/A (Unknown ID)"
            if report.applied_template_id:
                found_template = next(
                    (t for t in self.main_app_ref.templates_list if t.template_id == report.applied_template_id), None)
                if found_template:
                    template_name = found_template.name
                else:
                    template_name = f"ID: {report.applied_template_id}"
            self.reports_table.setItem(row, 1, QTableWidgetItem(template_name))
            self.reports_table.setItem(row, 2, QTableWidgetItem(report.timestamp))
            self.reports_table.setItem(row, 3, QTableWidgetItem(str(len(report.field_results))))
            self.reports_table.item(row, 0).setData(Qt.UserRole, report)

    def view_selected_doc_report(self):
        selected_rows = self.reports_table.selectionModel().selectedRows()
        if not selected_rows: QMessageBox.information(self, "View Report", "Please select a report to view."); return

        report_to_view: DocumentRunReport = self.reports_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        if report_to_view:
            base_pdf_path = self.main_app_ref.runner_tab.current_folder_path
            if not base_pdf_path and report_to_view.source_pdf_path:
                if os.path.isabs(report_to_view.source_pdf_path):  # Should be basename from storage
                    # This case is less likely if source_pdf_path from JSON is always basename
                    base_pdf_path = os.path.dirname(report_to_view.source_pdf_path)
                    # report_to_view.source_pdf_path = os.path.basename(report_to_view.source_pdf_path) # Ensure basename
                else:  # If it's relative and no base_pdf_path, it's problematic
                    print(
                        f"Warning: Cannot determine full path for report PDF '{report_to_view.source_pdf_path}' without a base folder in Runner tab.")

            dialog = ReportViewerDialog(report_to_view, base_pdf_path, self)
            dialog.reportUpdated.connect(self.handle_doc_report_updated)
            dialog.exec_()

    def handle_doc_report_updated(self, updated_report: DocumentRunReport):
        save_document_run_report(updated_report)
        self.load_and_display_doc_reports()
        QMessageBox.information(self, "Report Updated",
                                f"Changes to report for '{updated_report.source_pdf_path}' have been saved.")


class MainWindow(QMainWindow):
    templates_updated_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Data Extraction - Template Based")
        self.setGeometry(100, 100, 1450, 900)  # Adjusted width slightly
        self.setStyleSheet(STYLESHEET)

        self.templates_list: list[TemplateDefinition] = load_templates()

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.runner_tab = RunnerTab(self)
        self.tab_widget.addTab(self.runner_tab, "Batch Runner")

        # TemplateConfigurationTab is now correctly imported and used
        self.template_config_tab = TemplateConfigurationTab(self.templates_list)
        self.template_config_tab.templates_updated.connect(self.on_templates_changed_in_config)
        self.tab_widget.addTab(self.template_config_tab, "Template Configuration")

        self.report_summary_tab = RunReportSummaryTab(self)
        self.tab_widget.addTab(self.report_summary_tab, "Extraction Reports")

        self.statusBar().showMessage("Ready. Define templates in 'Template Configuration'.")
        self.templates_updated_signal.emit(self.templates_list)  # Initial emit

    def on_templates_changed_in_config(self, updated_templates_list: list[TemplateDefinition]):
        self.templates_list[:] = updated_templates_list
        save_templates(self.templates_list)
        self.templates_updated_signal.emit(self.templates_list)
        self.statusBar().showMessage("Templates configuration updated and saved.")

    def refresh_report_summary_tab(self):
        self.report_summary_tab.load_and_display_doc_reports()
        self.statusBar().showMessage("Batch run complete. Reports list updated.")

    def closeEvent(self, event):
        save_templates(self.templates_list)
        if hasattr(self.template_config_tab, 'pdf_processor') and self.template_config_tab.pdf_processor:
            self.template_config_tab.pdf_processor.close()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 9))
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())