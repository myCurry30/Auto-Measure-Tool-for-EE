import os
import win32com.client
import pythoncom


class EasyExcel:
    """A utility to make it easier to get at Excel.  Remembering
    to save the data is your problem, as is  error handling.
    Operates on one workbook at a time."""

    def __init__(self, filename=None):
        # 初始化COM
        pythoncom.CoInitialize()

        # 创建Excel应用
        self.xlApp = win32com.client.Dispatch('Excel.Application')
        if filename:
            self.filename = filename
            print(f"Opening Excel file: {filename}")
            self.xlBook = self.xlApp.Workbooks.Open(filename)
            self.xlApp.Visible = True
            # 确保Excel窗口在前台
            self._activate_excel_window()
        else:
            self.xlBook = self.xlApp.Workbooks.Add()
            self.filename = ''
            self.xlApp.Visible = True
            self._activate_excel_window()

    def save(self, newfilename=None):
        if newfilename:
            self.filename = newfilename
            self.xlBook.SaveAs(newfilename)
        else:
            self.xlBook.Save()

    def close(self):
        try:
            # 关闭工作簿
            self.xlBook.Close(SaveChanges=0)
            # 释放Excel应用
            if hasattr(self, 'xlApp'):
                self.xlApp.Visible = False
                self.xlApp.Quit()
                del self.xlApp
            # 释放COM
            pythoncom.CoUninitialize()
            print("[EasyExcel] Excel closed successfully")
        except Exception as e:
            print(f"[EasyExcel] Error closing Excel: {e}")
            # 确保资源被释放
            if hasattr(self, 'xlApp'):
                try:
                    self.xlApp.Quit()
                    del self.xlApp
                except:
                    pass
            pythoncom.CoUninitialize()

    def getCell(self, sheet, row, col):
        """Read cell value. For merged cells, returns the top-left value."""
        sht = self.xlBook.Worksheets(sheet)
        sht.Activate()
        cell = sht.Cells(row, col)
        # MergeArea.Cells(1,1) is the top-left cell of the merged range
        # (for non-merged cells, MergeArea is just the cell itself)
        return cell.MergeArea.Cells(1, 1).Value

    def setCell(self, sheet, row, col, value):
        sht = self.xlBook.Worksheets(sheet)
        sht.Activate()
        sht.Cells(row, col).Value = value

    def getRange(self, sheet, row1, col1, row2, col2):
        sht = self.xlBook.Worksheets(sheet)
        sht.Activate()
        return sht.Range(sht.Cells(row1, col1), sht.Cells(row2, col2)).Value

    def _col_letter(self, n):
        """1→A, 26→Z, 27→AA, ..."""
        s = ''
        while n > 0:
            n, r = divmod(n - 1, 26)
            s = chr(65 + r) + s
        return s

    def addPicture(self, sheet, PictureName, row, left_offset, Top_offset, width, height,
                   flag_Test_items=0, flag_monotony_direction=1, pic_cols=None):
        """Insert picture into Excel cell.

        Args:
            sheet: Sheet name
            PictureName: Image file path
            row: Target row
            left_offset: Left offset from cell
            Top_offset: Top offset from cell
            width: Image width (0 to use cell width)
            height: Image height (0 to use cell height)
            flag_Test_items: "sequence" or "monotony"
            flag_monotony_direction: 1=Positive/Rise, 0=Negative/Fall (for monotony)
            pic_cols: Optional tuple (seq_col, mono_p_col, mono_n_col)
        """
        sht = self.xlBook.Worksheets(sheet)
        sht.Activate()
        if flag_Test_items == "monotony":
            target_row = row
            if pic_cols:
                col_num = pic_cols[1] if flag_monotony_direction == 1 else pic_cols[2]
            else:
                col_num = 17 if flag_monotony_direction == 1 else 18
            cell_addr = self._col_letter(col_num) + str(target_row)
            Width = sht.Cells(target_row, col_num).Width
            Height = sht.Cells(target_row, col_num).Height
            cell = sht.Range(cell_addr)
        else:
            target_row = row
            col_num = pic_cols[0] if pic_cols else 9
            cell_addr = self._col_letter(col_num) + str(target_row)
            Width = sht.Cells(target_row, col_num).Width
            Height = sht.Cells(target_row, col_num).Height
            cell = sht.Range(cell_addr)
        print(f"[EasyExcel] addPicture: type={flag_Test_items}, dir={flag_monotony_direction}, "
              f"cell={cell_addr}, row={target_row}, W={Width:.0f}, H={Height:.0f}")
        cell.Select()
        cell.ClearFormats()
        sht.Shapes.AddPicture(PictureName, LinkToFile=False, SaveWithDocument=True,
                              Left=cell.Left + left_offset, Top=cell.Top + Top_offset,
                              Width=Width, Height=Height)
        print(f"[EasyExcel] addPicture: inserted at {cell_addr}")

    def get_sheet_names(self):
        """Return a list of all sheet names in the workbook."""
        return [sheet.Name for sheet in self.xlBook.Worksheets]

    def activate_sheet(self, sheet_name):
        """Activate a specific sheet and ensure Excel window is visible."""
        try:
            # Ensure Excel is visible
            self.xlApp.Visible = True

            # Set Excel window size and position (larger window)
            try:
                # 尝试设置窗口大小和位置
                import ctypes
                hwnd = self.xlApp.Hwnd
                if hwnd:
                    # 设置窗口位置和大小 (最大化或大窗口)
                    # SW_MAXIMIZE = 3
                    ctypes.windll.user32.ShowWindow(hwnd, 3)
                    # 确保窗口在最前面
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
            except:
                # 如果设置失败，至少确保窗口可见
                pass

            # Wait a moment for window to be ready
            import time
            time.sleep(0.5)

            # Activate the specific sheet
            sht = self.xlBook.Worksheets(sheet_name)
            sht.Activate()

            # Bring Excel to front again
            self._activate_excel_window()

            # Scroll to top left of the sheet
            try:
                sht.Cells(1, 1).Select()
            except:
                pass

            print(f"[EasyExcel] Activated sheet: {sheet_name}")
            return True
        except Exception as e:
            print(f"[EasyExcel] Error activating sheet {sheet_name}: {e}")
            return False

    def _activate_excel_window(self):
        """Bring Excel window to the front and activate it."""
        try:
            # 尝试多种方法确保Excel窗口在前台
            import time

            # 方法1: 尝试激活Excel应用
            try:
                self.xlApp.Activate()
                time.sleep(0.1)  # 短暂等待
            except:
                pass

            # 方法2: 使用Windows API设置窗口大小和位置
            try:
                import ctypes
                # 获取Excel窗口句柄
                hwnd = self.xlApp.Hwnd
                if hwnd:
                    # 尝试最大化窗口 (SW_MAXIMIZE = 3)
                    if ctypes.windll.user32.ShowWindow(hwnd, 3):
                        print("[EasyExcel] Excel window maximized")
                    else:
                        # 如果最大化失败，设置一个较大的窗口
                        # 获取屏幕尺寸
                        screen_width = ctypes.windll.user32.GetSystemMetrics(0)  # SM_CXSCREEN
                        screen_height = ctypes.windll.user32.GetSystemMetrics(1)  # SM_CYSCREEN

                        # 设置窗口大小为屏幕的80%
                        window_width = int(screen_width * 0.8)
                        window_height = int(screen_height * 0.8)

                        # 设置窗口位置（居中）
                        x = (screen_width - window_width) // 2
                        y = (screen_height - window_height) // 2

                        # 设置窗口位置和大小
                        ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, window_width, window_height, 0)
                        print(f"[EasyExcel] Excel window resized to {window_width}x{window_height}")

                    # 将窗口置于前台
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception as e:
                print(f"[EasyExcel] Error setting window size: {e}")
                # 如果设置大小失败，至少确保窗口可见
                pass

            # 方法3: 如果上面都失败，确保窗口可见
            self.xlApp.Visible = True

            print("[EasyExcel] Excel window brought to front")
        except Exception as e:
            print(f"[EasyExcel] Error bringing Excel to front: {e}")

    def cpSheet(self):
        shts = self.xlBook.Worksheets
        shts(1).Copy(None, shts(1))