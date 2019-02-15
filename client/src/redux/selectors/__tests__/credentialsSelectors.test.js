import credentialsSelectors from '../credentialsSelectors';
import apiTypes from '../../../constants/apiConstants';

describe('CredentialsSelectors', () => {
  it('Should return specific selectors', () => {
    expect(credentialsSelectors).toMatchSnapshot('selectors');
  });

  it('Should map a response to a consumable dropdown format', () => {
    const state = {
      credentials: {
        view: {
          credentials: [
            {
              [apiTypes.API_RESPONSE_CREDENTIAL_NAME]: 'Lorem',
              [apiTypes.API_RESPONSE_CREDENTIAL_CRED_TYPE]: 'network',
              [apiTypes.API_RESPONSE_CREDENTIAL_ID]: 54
            },
            {
              [apiTypes.API_RESPONSE_CREDENTIAL_NAME]: 'Ipsum',
              [apiTypes.API_RESPONSE_CREDENTIAL_CRED_TYPE]: 'vcenter',
              [apiTypes.API_RESPONSE_CREDENTIAL_ID]: 1
            },
            {
              [apiTypes.API_RESPONSE_CREDENTIAL_NAME]: 'Dolor',
              [apiTypes.API_RESPONSE_CREDENTIAL_CRED_TYPE]: 'satellite',
              [apiTypes.API_RESPONSE_CREDENTIAL_ID]: 200
            }
          ]
        }
      }
    };

    expect(credentialsSelectors.credentialsDropdown(state)).toMatchSnapshot('credentialsDropdown');
  });
});
