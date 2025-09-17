Sub ExtractByCode()
    Dim targetCode As String
    Dim sourceSheet As Worksheet
    Dim targetSheet As Worksheet
    Dim lastRow As Long
    Dim i As Long
    Dim targetRow As Long
    
    ' mainシートのB2セルから銘柄コードを取得
    Set targetSheet = ThisWorkbook.Sheets("main")
    targetCode = CStr(targetSheet.Range("B2").Value)
    
    If targetCode = "" Then
        MsgBox "mainシートのB2セルに銘柄コードを入力してください。", vbExclamation
        Exit Sub
    End If
    
    ' シートを設定
    Set sourceSheet = ThisWorkbook.Sheets("html_summary")
    
    ' mainシートの45行目以降をクリア
    Dim clearRange As Range
    Set clearRange = targetSheet.Range("A45:AC" & targetSheet.Rows.Count)
    clearRange.Clear
    
    ' ヘッダーをコピー（44行目に配置）
    sourceSheet.Rows(1).Copy Destination:=targetSheet.Rows(44)
    
    ' データの最終行を取得
    lastRow = sourceSheet.Cells(sourceSheet.Rows.Count, "C").End(xlUp).Row
    
    ' 対象の銘柄データを抽出（45行目から開始）
    targetRow = 45
    For i = 2 To lastRow
        If CStr(sourceSheet.Cells(i, 3).Value) = targetCode Then ' C列がcode
            sourceSheet.Rows(i).Copy Destination:=targetSheet.Rows(targetRow)
            targetRow = targetRow + 1
        End If
    Next i
    
    If targetRow = 45 Then
        MsgBox "銘柄コード " & targetCode & " のデータが見つかりませんでした。", vbInformation
    Else
        MsgBox "銘柄コード " & targetCode & " のデータを " & (targetRow - 45) & " 件抽出しました。", vbInformation
        targetSheet.Activate
    End If
End Sub

' 複数銘柄を一度に抽出する関数
Sub ExtractMultipleCodes()
    Dim codes As String
    Dim codeArray() As String
    Dim sourceSheet As Worksheet
    Dim targetSheet As Worksheet
    Dim lastRow As Long
    Dim i As Long, j As Long
    Dim targetRow As Long
    Dim codeDict As Object
    
    ' 抽出したい銘柄コードをカンマ区切りで入力
    codes = InputBox("抽出したい銘柄コードをカンマ区切りで入力してください" & vbCrLf & "例: 13010,13320,13330", "複数銘柄コード入力")
    
    If codes = "" Then
        MsgBox "銘柄コードが入力されませんでした。", vbExclamation
        Exit Sub
    End If
    
    ' カンマで分割
    codeArray = Split(codes, ",")
    
    ' Dictionary作成（高速化のため）
    Set codeDict = CreateObject("Scripting.Dictionary")
    For i = 0 To UBound(codeArray)
        codeDict(Trim(codeArray(i))) = True
    Next i
    
    ' シートを設定
    Set sourceSheet = ThisWorkbook.Sheets("html_summary")
    Set targetSheet = ThisWorkbook.Sheets("main")
    
    ' mainシートの3行目以降をクリア（1行目は銘柄コード、2行目はヘッダー用）
    Dim clearRange As Range
    Set clearRange = targetSheet.Range("A3:AC" & targetSheet.Rows.Count)
    clearRange.Clear
    
    ' ヘッダーをコピー（2行目に配置）
    sourceSheet.Rows(1).Copy Destination:=targetSheet.Rows(2)
    
    ' データの最終行を取得
    lastRow = sourceSheet.Cells(sourceSheet.Rows.Count, "C").End(xlUp).Row
    
    ' 対象の銘柄データを抽出（3行目から開始）
    targetRow = 3
    For i = 2 To lastRow
        If codeDict.Exists(CStr(sourceSheet.Cells(i, 3).Value)) Then ' C列がcode
            sourceSheet.Rows(i).Copy Destination:=targetSheet.Rows(targetRow)
            targetRow = targetRow + 1
        End If
    Next i
    
    If targetRow = 3 Then
        MsgBox "指定された銘柄コードのデータが見つかりませんでした。", vbInformation
    Else
        MsgBox (targetRow - 2) & " 件のデータを抽出しました。", vbInformation
        targetSheet.Activate
    End If
End Sub