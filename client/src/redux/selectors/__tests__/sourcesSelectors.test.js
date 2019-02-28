import sourcesSelectors from '../sourcesSelectors';
import apiTypes from '../../../constants/apiConstants';

describe('SourcesSelectors', () => {
  it('Should return specific selectors', () => {
    expect(sourcesSelectors).toMatchSnapshot('selectors');
  });

  it('Should map a source to consumable props', () => {
    const state = {
      addSourceWizard: {
        source: {
          [apiTypes.API_RESPONSE_SOURCE_CREDENTIALS]: [15],
          [apiTypes.API_RESPONSE_SOURCE_HOSTS]: ['192.168.0.1'],
          [apiTypes.API_RESPONSE_SOURCE_ID]: 1,
          [apiTypes.API_RESPONSE_SOURCE_NAME]: 'lorem',
          [apiTypes.API_RESPONSE_SOURCE_OPTIONS]: {
            [apiTypes.API_RESPONSE_SOURCE_OPTIONS_PARAMIKO]: false,
            [apiTypes.API_RESPONSE_SOURCE_OPTIONS_DISABLE_SSL]: false,
            [apiTypes.API_RESPONSE_SOURCE_OPTIONS_SSL_PROTOCOL]: false,
            [apiTypes.API_RESPONSE_SOURCE_OPTIONS_SSL_CERT]: false
          },
          [apiTypes.API_RESPONSE_SOURCE_PORT]: 22,
          [apiTypes.API_RESPONSE_SOURCE_SOURCE_TYPE]: 'network'
        }
      }
    };

    expect(sourcesSelectors.sourceDetail(state)).toMatchSnapshot('sourceDetail');

    const updatedState = {
      addSourceWizard: {
        source: {
          [apiTypes.API_RESPONSE_SOURCE_CREDENTIALS]: [
            {
              [apiTypes.API_RESPONSE_SOURCE_CREDENTIALS_ID]: 10
            }
          ],
          [apiTypes.API_RESPONSE_SOURCE_HOSTS]: ['192.168.0.1'],
          [apiTypes.API_RESPONSE_SOURCE_ID]: 1,
          [apiTypes.API_RESPONSE_SOURCE_NAME]: 'lorem',
          [apiTypes.API_RESPONSE_SOURCE_OPTIONS]: {
            [apiTypes.API_RESPONSE_SOURCE_OPTIONS_PARAMIKO]: false,
            [apiTypes.API_RESPONSE_SOURCE_OPTIONS_DISABLE_SSL]: false,
            [apiTypes.API_RESPONSE_SOURCE_OPTIONS_SSL_PROTOCOL]: false,
            [apiTypes.API_RESPONSE_SOURCE_OPTIONS_SSL_CERT]: false
          },
          [apiTypes.API_RESPONSE_SOURCE_PORT]: 22,
          [apiTypes.API_RESPONSE_SOURCE_SOURCE_TYPE]: 'network'
        }
      }
    };

    expect(sourcesSelectors.sourceDetail(updatedState)).toMatchSnapshot('sourceDetail updated');
  });

  it('Should minimally map an undefined source or properties', () => {
    const state = {
      addSourceWizard: {
        source: undefined
      }
    };

    expect(sourcesSelectors.sourceDetail(state)).toMatchSnapshot('sourceDetail undefined');

    state.addSourceWizard.source = {
      [apiTypes.API_RESPONSE_SOURCE_CREDENTIALS]: undefined,
      [apiTypes.API_RESPONSE_SOURCE_HOSTS]: undefined,
      [apiTypes.API_RESPONSE_SOURCE_ID]: undefined,
      [apiTypes.API_RESPONSE_SOURCE_NAME]: undefined,
      [apiTypes.API_RESPONSE_SOURCE_OPTIONS]: {
        [apiTypes.API_RESPONSE_SOURCE_OPTIONS_PARAMIKO]: undefined,
        [apiTypes.API_RESPONSE_SOURCE_OPTIONS_DISABLE_SSL]: undefined,
        [apiTypes.API_RESPONSE_SOURCE_OPTIONS_SSL_PROTOCOL]: undefined,
        [apiTypes.API_RESPONSE_SOURCE_OPTIONS_SSL_CERT]: undefined
      },
      [apiTypes.API_RESPONSE_SOURCE_PORT]: undefined,
      [apiTypes.API_RESPONSE_SOURCE_SOURCE_TYPE]: undefined
    };

    expect(sourcesSelectors.sourceDetail(state)).toMatchSnapshot('sourceDetail properties undefined');
  });
});
