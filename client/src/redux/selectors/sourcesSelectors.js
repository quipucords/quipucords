import { createSelector } from 'reselect';
import _get from 'lodash/get';
import helpers from '../../common/helpers';
import apiTypes from '../../constants/apiConstants';

/**
 * Map a new source object to consumable prop names
 */
const sourceDetail = state => state.addSourceWizard.source;

/**
 * Map an edit source object to consumable prop names
 */
const editSourceDetail = state => state.addSourceWizard.editSource;

const sourceDetailSelector = createSelector(
  [sourceDetail, editSourceDetail],
  (source, editSource) => {
    const updateSource = Object.assign({}, editSource || {}, source || {});
    const newSource = {};

    if (updateSource) {
      /**
       * Allow for an edit source with credentials in the form of
       * [{ id:Number, type:String, name:String }]
       * Or a new source in the form of
       * [id]
       */
      helpers.setPropIfDefined(
        newSource,
        ['credentials'],
        _get(updateSource, apiTypes.API_RESPONSE_SOURCE_CREDENTIALS, []).map(
          cred => cred[apiTypes.API_RESPONSE_SOURCE_CREDENTIALS_ID] || cred
        )
      );

      helpers.setPropIfDefined(newSource, ['hosts'], updateSource[apiTypes.API_RESPONSE_SOURCE_HOSTS]);
      helpers.setPropIfDefined(newSource, ['id'], updateSource[apiTypes.API_RESPONSE_SOURCE_ID]);
      helpers.setPropIfDefined(newSource, ['name'], updateSource[apiTypes.API_RESPONSE_SOURCE_NAME]);

      if (updateSource[apiTypes.API_RESPONSE_SOURCE_OPTIONS]) {
        helpers.setPropIfDefined(
          newSource,
          ['optionSslCert'],
          _get(updateSource[apiTypes.API_RESPONSE_SOURCE_OPTIONS], apiTypes.API_RESPONSE_SOURCE_OPTIONS_SSL_CERT)
        );

        helpers.setPropIfDefined(
          newSource,
          ['optionSslProtocol'],
          _get(updateSource[apiTypes.API_RESPONSE_SOURCE_OPTIONS], apiTypes.API_RESPONSE_SOURCE_OPTIONS_SSL_PROTOCOL)
        );

        helpers.setPropIfDefined(
          newSource,
          ['optionDisableSsl'],
          _get(updateSource[apiTypes.API_RESPONSE_SOURCE_OPTIONS], apiTypes.API_RESPONSE_SOURCE_OPTIONS_DISABLE_SSL)
        );

        helpers.setPropIfDefined(
          newSource,
          ['optionParamiko'],
          _get(updateSource[apiTypes.API_RESPONSE_SOURCE_OPTIONS], apiTypes.API_RESPONSE_SOURCE_OPTIONS_PARAMIKO)
        );
      }

      helpers.setPropIfDefined(newSource, 'port', updateSource[apiTypes.API_RESPONSE_SOURCE_PORT]);
      helpers.setPropIfDefined(newSource, ['type'], updateSource[apiTypes.API_RESPONSE_SOURCE_SOURCE_TYPE]);

      if (newSource.hosts && newSource.hosts.length) {
        newSource.hostsMultiple = newSource.hosts.join(',\n');
        newSource.hostsSingle = `${newSource.hosts[0]}:${newSource.port || ''}`;
      }
    }

    return newSource;
  }
);

const makeSourceDetailSelector = () => sourceDetailSelector;

const sourcesSelectors = {
  sourceDetail: sourceDetailSelector,
  makeSourceDetail: makeSourceDetailSelector
};

export { sourcesSelectors as default, sourcesSelectors, sourceDetailSelector, makeSourceDetailSelector };
