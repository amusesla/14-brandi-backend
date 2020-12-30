import json
import flask

from flask                   import jsonify, request
from flask.views             import MethodView

from utils.connection        import get_connection
from utils.custom_exceptions import DatabaseCloseFail
from utils.rules             import (
    RequiredFieldRule,
    NumberRule,
    AlphabeticRule
)
from flask_request_validator import (
    Param,
    JSON,
    validate_params,
    FORM,
    MinLength,
    MaxLength
)


class CreateProductView(MethodView):
    """ Presentation Layer
    
        Attributes:
            service  : CreateProductService 클래스
            database : app.config['DB']에 담겨있는 정보(데이터베이스 관련 정보)
            
        Author: 심원두
        
        History:
            2020-12-29(심원두): 초기 생성. products insert, product_code updated, product_histories 생성 기능 작성
            2020-12-30(심원두): 각 Param rules 추가, stock insert 기능 작성.
    """
    
    def __init__(self, service, database):
        self.service = service
        self.database = database
    
    @validate_params(
        Param('seller_id',              FORM, int,  required=True,  rules=[RequiredFieldRule()]),
        Param('account_id',             FORM, int,  required=True,  rules=[RequiredFieldRule()]),
        Param('is_sale',                FORM, bool, required=True,  rules=[RequiredFieldRule()]),
        Param('is_display',             FORM, bool, required=True,  rules=[RequiredFieldRule()]),
        Param('main_category_id',       FORM, int,  required=True,  rules=[RequiredFieldRule()]),
        Param('sub_category_id',        FORM, int,  required=True,  rules=[RequiredFieldRule()]),
        Param('is_product_notice',      FORM, bool, required=True,  rules=[RequiredFieldRule()]),
        Param('manufacturer',           FORM, str,  required=False, rules=[MaxLength(30)]),
        Param('manufacturing_date',     FORM, str,  required=False),
        Param('product_origin_type_id', FORM, str,  required=False),
        Param('product_name',           FORM, str,  required=True,  rules=[RequiredFieldRule(), MaxLength(100)]),
        Param('description',            FORM, str,  required=True,  rules=[RequiredFieldRule(), MaxLength(200)]),
        Param('detail_information',     FORM, str,  required=True,  rules=[RequiredFieldRule()]),
        Param('options',                FORM, list, required=True),
        Param('minimum_quantity',       FORM, int,  required=False, rules=[RequiredFieldRule()]),
        Param('maximum_quantity',       FORM, int,  required=False, rules=[RequiredFieldRule()]),
        Param('origin_price',           FORM, str,  required=True,  rules=[RequiredFieldRule()]),
        Param('discount_rate',          FORM, str,  required=True),
        Param('discounted_price',       FORM, str,  required=True),
        Param('discount_start_date',    FORM, str,  required=False),
        Param('discount_end_date',      FORM, str,  required=False)
    )
    def post(self, *args):
        """POST 메소드: 상품 정보 등록
            
            Args: None
            
            Form-Data: (
                seller_id',
                account_id',
                is_sale',
                is_display',
                main_category_id',
                sub_category_id',
                is_product_notice',
                manufacturer',
                manufacturing_date',
                product_origin_type_id',
                product_name',
                description',
                detail_information',
                options',
                minimum_quantity',
                maximum_quantity',
                origin_price',
                discount_rate',
                discounted_price',
                discount_start_date',
                discount_end_date',
            )
            
            Author: 심원두
            
            Returns:
                200, {'message': 'success'}                                                          : 상품 정보 등록 성공
                
            Raises:
                400, {'message': 'invalid_parameter', 'errorMessage': str(e)}                        : 잘못된 요청값
                400, {'message': 'key_error', 'errorMessage': 'key_error_' + format(e)}              : 잘못 입력된 키값
                403, {'message': 'user_already_exist', errorMessage': 'already_exist' + _중복 데이터}   : 중복 유저 생성 실패
                500, {'message': 'product_create_denied', 'errorMessage': 'account_create_fail'}        : 유저 생성 실패
                500, {'message': 'user_create_denied', 'errorMessage': 'user_create_fail'}           : 유저 생성 실패
                
                500, {'message': 'database_connection_fail', 'errorMessage': 'database_close_fail'}  : 커넥션 종료 실패
                500, {'message': 'database_error', 'errorMessage': 'database_error_' + format(e)}    : 데이터베이스 에러
                500, {'message': 'internal_server_error', 'errorMessage': format(e)})                : 서버 에러
            History:
                2020-12-29(심원두): 초기 생성
                2020-12-30(심원두):
        """
        
        data = {
            'seller_id'              : request.form.get('seller_id'),
            'account_id'             : request.form.get('account_id'),
            'is_sale'                : request.form.get('is_sale'),
            'is_display'             : request.form.get('is_display'),
            'main_category_id'       : request.form.get('main_category_id'),
            'sub_category_id'        : request.form.get('sub_category_id'),
            'is_product_notice'      : request.form.get('is_product_notice'),
            'manufacturer'           : request.form.get('manufacturer', None),
            'manufacturing_date'     : request.form.get('manufacturing_date', None),
            'product_origin_type_id' : request.form.get('product_origin_type_id', None),
            'product_name'           : request.form.get('product_name'),
            'description'            : request.form.get('description'),
            'detail_information'     : request.form.get('detail_information'),
            'minimum_quantity'       : request.form.get('minimum_quantity'),
            'maximum_quantity'       : request.form.get('maximum_quantity'),
            'origin_price'           : request.form.get('origin_price'),
            'discount_rate'          : request.form.get('discount_rate'),
            'discounted_price'       : request.form.get('discounted_price'),
            'discount_start_date'    : request.form.get('discount_start_date', None),
            'discount_end_date'      : request.form.get('discount_end_date', None),
        }
        
        product_images = flask.request.files.getlist("imageFiles")
        stocks = json.loads(request.form.get('options'))
        
        try:
            connection = get_connection(self.database)
            
            # products 테이블 insert
            product_id = self.service.create_product(connection, data)
            
            # products 테이블 update (product_code)
            self.service.update_product_code(connection, product_id)
            
            # product_images 테이블 insert
            # TODO : 프론트와 상의
            # self.service.insert_product_images(connection, product_id, product_images)
            
            # stock 테이블 insert
            self.service.insert_stock(connection, product_id, stocks)
            
            # product_histories 테이블 insert
            self.service.insert_product_history(connection, product_id, data)
            
            connection.commit()
            
            return jsonify({'message': 'success'}), 200
        
        except Exception as e:
            connection.rollback()
            raise e
        
        finally:
            try:
                if connection:
                    connection.close()
            except Exception:
                raise DatabaseCloseFail('database close fail')