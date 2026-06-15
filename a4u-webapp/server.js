const express = require('express');
const multer = require('multer');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;
const uploadFolder = path.join(__dirname, 'uploads');

if (!fs.existsSync(uploadFolder)) {
    fs.mkdirSync(uploadFolder, { recursive: true });
}

const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, uploadFolder);
    },
    filename: function (req, file, cb) {
        const timestamp = Date.now();
        const sanitized = file.originalname.replace(/[^a-zA-Z0-9._-]/g, '-');
        cb(null, `${timestamp}-${sanitized}`);
    }
});

const upload = multer({
    storage,
    fileFilter: function (req, file, cb) {
        const allowedTypes = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ];
        if (allowedTypes.includes(file.mimetype)) {
            cb(null, true);
        } else {
            cb(new Error('PDF, DOC, DOCX 파일만 업로드할 수 있습니다.'));
        }
    },
    limits: {
        fileSize: 10 * 1024 * 1024
    }
});

app.use(cors());
app.use(express.static(path.join(__dirname)));

app.post('/upload-resume', upload.single('resumeFile'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ success: false, message: '파일이 필요합니다.' });
    }

    res.json({
        success: true,
        originalName: req.file.originalname,
        savedName: req.file.filename,
        size: req.file.size,
        mimeType: req.file.mimetype,
        uploadedAt: new Date().toISOString()
    });
});

app.use((err, req, res, next) => {
    if (err instanceof multer.MulterError) {
        return res.status(400).json({ success: false, message: err.message });
    }
    res.status(400).json({ success: false, message: err.message || '알 수 없는 오류가 발생했습니다.' });
});

app.listen(PORT, () => {
    console.log(`Server is running at http://localhost:${PORT}`);
    console.log('Open /k/select.html to test resume upload.');
});