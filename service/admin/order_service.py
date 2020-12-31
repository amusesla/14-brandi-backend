from utils.custom_exceptions import OrderFilterNotExist, NoPermissionGetOrderList

class OrderService:
    """ Business Layer
            Attributes:
                get_order_list_dao: OrderDao 클래스

            Author: 김민서

            History:
                2020-20-29(김민서): 초기 생성
                2020-12-30(김민서): 1차 수정
                2020-12-31(김민서): 2차 수정
    """
    def __init__(self, master_order_dao):
        self.master_order_dao = master_order_dao

    def get_orders_service(self, connection, data):
        try:
            if data['permission'] != 1 or 2:
                raise NoPermissionGetOrderList('no_permission_to_get_order_list')

            data['page']  = (data['page'] - 1) * data['length']
            date_inputs   = (data['start_date'], data['end_date'])
            filter_inputs = (data['number'], data['detail_number'], data['sender_name'], data['sender_phone'],
                             data['seller_name'], ['product_name'])

            if not (date_inputs and filter_inputs):
                raise OrderFilterNotExist('must_be_date_inputs_or_filter_inputs')

            if data['sender_phone']:
                data['sender_phone'] = data['sender_phone'].replace("-", "")
            if data['product_name']:
                data['product_name'] = '%' + data['product_name'] + '%'

            return self.master_order_dao.get_order_list_dao(connection, data)

        except KeyError:
            return 'key_error'