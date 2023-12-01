# get user_if from order_id 
def get_user_id_from_order_id(order_id: str):
    return order_id.split('_')[0]
