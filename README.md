# 衣橱管理API (dada-api)

一个基于Flask的衣橱管理系统后端API，提供用户管理和服装的增删改查功能。

## 功能特性

- 用户管理
  - 注册
  - 登录
  - 获取用户信息
  - 更新用户昵称和密码

- 服装管理
  - 添加服装
  - 获取所有服装
  - 获取单个服装详情
  - 更新服装信息
  - 删除服装
  - 记录穿着次数

## 技术栈

- Python 3.13+
- Flask 3.1.2+
- Flask-SQLAlchemy 3.1.1+ (SQLite数据库)
- Flask-CORS 6.0.1+
- PyJWT 2.10.1+ (用户认证)
- python-dotenv 1.1.1+

## 安装步骤

1. 克隆仓库

2. 安装依赖
   ```bash
   pip install -e .
   ```

3. 创建.env文件
   在项目根目录创建.env文件，包含以下内容：
   ```
   FLASK_APP=main.py
   FLASK_ENV=development
   JWT_SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///dada.db
   ```
   > 提示：JWT_SECRET_KEY应该设置为一个安全的随机字符串

4. 运行应用
   ```bash
   python main.py
   ```

## API文档

### 用户接口

#### 注册
- **URL**: `/api/register`
- **方法**: `POST`
- **请求体**: 
  ```json
  {
    "username": "string",
    "password": "string",
    "nickname": "string" (可选)
  }
  ```
- **响应**: 
  - 成功: `201 Created`
  - 失败: `400 Bad Request`

#### 登录
- **URL**: `/api/login`
- **方法**: `POST`
- **请求体**: 
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **响应**: 
  - 成功: `200 OK`，返回JWT令牌
  - 失败: `401 Unauthorized`

#### 获取当前用户信息
- **URL**: `/api/user`
- **方法**: `GET`
- **认证**: 需要JWT令牌 (在Authorization头中添加 `Bearer <token>`)
- **响应**: `200 OK`，返回用户信息

#### 更新用户信息
- **URL**: `/api/user`
- **方法**: `PUT`
- **认证**: 需要JWT令牌
- **请求体**: 
  ```json
  {
    "nickname": "string" (可选),
    "password": "string" (可选)
  }
  ```
- **响应**: `200 OK`

### 服装接口

所有服装接口都需要JWT认证。

#### 添加服装
- **URL**: `/api/clothes`
- **方法**: `POST`
- **请求体**: 
  ```json
  {
    "name": "string",
    "image_url": "string" (可选),
    "category": "string",
    "purchase_date": "YYYY-MM-DD" (可选),
    "price": number (可选),
    "wear_count": integer (可选),
    "washing_method": "string" (可选),
    "status": "string" (可选，默认：良好)
  }
  ```
- **响应**: `201 Created`，返回创建的服装信息

#### 获取所有服装
- **URL**: `/api/clothes`
- **方法**: `GET`
- **响应**: `200 OK`，返回服装列表

#### 获取单个服装
- **URL**: `/api/clothes/<id>`
- **方法**: `GET`
- **响应**: `200 OK`，返回服装详情

#### 更新服装
- **URL**: `/api/clothes/<id>`
- **方法**: `PUT`
- **请求体**: 与添加服装相同，但只需要包含要更新的字段
- **响应**: `200 OK`

#### 删除服装
- **URL**: `/api/clothes/<id>`
- **方法**: `DELETE`
- **响应**: `200 OK`

#### 增加穿着次数
- **URL**: `/api/clothes/<id>/wear`
- **方法**: `POST`
- **响应**: `200 OK`

## 数据库模型

### User
- `id`: 主键
- `username`: 用户名，唯一
- `password_hash`: 密码哈希
- `nickname`: 昵称
- `created_at`: 创建时间

### Clothing
- `id`: 主键
- `name`: 服装名称
- `image_url`: 图片URL
- `category`: 分类
- `purchase_date`: 购买日期
- `price`: 价格
- `wear_count`: 穿着次数
- `washing_method`: 洗涤方式
- `status`: 状态
- `created_at`: 创建时间
- `updated_at`: 更新时间
- `user_id`: 外键，关联用户

## 开发说明

- 开发环境下，服务器会自动重启以应用代码更改
- SQLite数据库文件会自动创建在项目根目录下
- 所有API响应都是JSON格式

## 许可证

MIT License