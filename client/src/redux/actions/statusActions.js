import { statusTypes } from '../constants';
import statusService from '../../services/statusService';

const getStatus = () => dispatch =>
  dispatch({
    type: statusTypes.STATUS_INFO,
    payload: statusService.getStatus()
  });

export { getStatus as default, getStatus };
