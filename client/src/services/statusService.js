import axios from 'axios';
import serviceConfig from './config';

const getStatus = () =>
  axios(
    serviceConfig(
      {
        url: process.env.REACT_APP_STATUS_SERVICE
      },
      false
    )
  );

const statusService = {
  getStatus
};

export { statusService as default, statusService, getStatus };
