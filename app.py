from flask import Flask, render_template, request
from PIL import Image
import numpy as np
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CHAR_PATTERN_MAP = {
    "000110100": '0', "100100001": '1', "001100001": '2', "101100000": '3',
    "000110001": '4', "100110000": '5', "001110000": '6', "000100101": '7',
    "100100100": '8', "001100100": '9', "100001001": 'A', "001001001": 'B',
    "101001000": 'C', "000011001": 'D', "100011000": 'E', "001011000": 'F',
    "000001101": 'G', "100001100": 'H', "001001100": 'I', "000011100": 'J',
    "100000011": 'K', "001000011": 'L', "101000010": 'M', "000010011": 'N',
    "100010010": 'O', "001010010": 'P', "000000111": 'Q', "100000110": 'R',
    "001000110": 'S', "000010110": 'T', "110000001": 'U', "011000001": 'V',
    "111000000": 'W', "010010001": 'X', "110010000": 'Y', "011010000": 'Z',
    "010000101": '-', "110000100": '.', "011000100": ' ', "010010100": '*',
    "010101000": '$', "010100010": '/', "010001010": '+', "000101010": '%'
}

def interpret_barcode(img):
    gray = np.array(img.convert('L'))
    if gray.shape[0] > gray.shape[1]:
        gray = np.rot90(gray, k=-1)
    thresh = (gray.min() + gray.max()) // 2
    bin_img = gray < thresh
    if np.count_nonzero(bin_img) > bin_img.size // 2:
        bin_img = ~bin_img
    ys, xs = np.nonzero(bin_img)
    if len(ys) == 0:
        return ""
    y1, y2 = ys.min(), ys.max()
    x1, x2 = xs.min(), xs.max()
    region = bin_img[y1:y2+1, x1:x2+1]
    row = region.shape[0] // 2
    line = region[row, :].astype(int)
    if line[0] == 0:
        idx = np.argmax(line)
        line = line[idx:]
    lens, col, count = [], line[0], 1
    for px in line[1:]:
        if px == col:
            count += 1
        else:
            lens.append(count)
            col = px
            count = 1
    lens.append(count)
    lens = np.array(lens, dtype=float)
    thin, thick = lens.min(), lens.max()
    for _ in range(5):
        is_thin = np.abs(lens - thin) < np.abs(lens - thick)
        if is_thin.sum() == 0 or (~is_thin).sum() == 0:
            return ""
        new_thin = lens[is_thin].mean()
        new_thick = lens[~is_thin].mean()
        if np.isclose(thin, new_thin) and np.isclose(thick, new_thick):
            break
        thin, thick = new_thin, new_thick
    limit = (thin + thick) / 2
    bits = ['1' if l > limit else '0' for l in lens]
    total = len(bits)
    usable = ((total + 1) // 10) * 10 - 1
    bits = bits[:usable]
    output = []
    symbols = (len(bits) + 1) // 10
    for j in range(symbols):
        i = j * 10
        patt = ''.join(bits[i:i+9])
        ch = CHAR_PATTERN_MAP.get(patt)
        if ch is None:
            return ""
        output.append(ch)
    if len(output) < 2 or output[0] != '*' or output[-1] != '*':
        return ""
    return ''.join(output[1:-1])

@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['barcode']
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            img = Image.open(filepath)
            result = interpret_barcode(img)
            return render_template('index.html', result=result, image=file.filename)
    return render_template('index.html', result=None)

if __name__ == '__main__':
    app.run(debug=True)
