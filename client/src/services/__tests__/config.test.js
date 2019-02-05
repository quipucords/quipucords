import cookies from 'js-cookie';
import * as service from '../config';

describe('ServiceConfig', () => {
  it('should export a specific number of methods and classes', () => {
    expect(Object.keys(service)).toHaveLength(2);
  });

  it('should export a default services config', () => {
    expect(service.serviceConfig).toBeDefined();

    cookies.set(process.env.REACT_APP_AUTH_TOKEN, 'spoof');

    const configObject = service.serviceConfig(
      {
        method: 'post',
        timeout: 3
      },
      true
    );

    expect(configObject.method).toEqual('post');
    expect(configObject.timeout).toEqual(3);
  });

  it('should export a default services config without authorization', () => {
    const configObject = service.serviceConfig({}, false);

    expect(configObject.headers[process.env.REACT_APP_AUTH_HEADER]).toBeUndefined();
  });
});
