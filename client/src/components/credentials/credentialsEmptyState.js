import React from 'react';
import PropTypes from 'prop-types';
import { Button, DropdownButton, EmptyState, Grid, MenuItem, Row } from 'patternfly-react';
import helpers from '../../common/helpers';

const CredentialsEmptyState = ({ onAddCredential, onAddSource }) => (
  <Grid fluid>
    <Row>
      <EmptyState className="full-page-blank-slate">
        <EmptyState.Icon />
        <EmptyState.Title>Welcome to {helpers.RH_BRAND && 'Red Hat'} Entitlements Reporting</EmptyState.Title>
        <EmptyState.Info>
          Credentials contain authentication information needed to scan a source. A credential includes <br />a username
          and a password or SSH key. Entitlements Reporting uses SSH to connect to servers <br /> on the network and
          uses credentials to access those servers.
        </EmptyState.Info>
        <EmptyState.Action>
          <DropdownButton bsStyle="primary" bsSize="large" title="Add Credential" pullRight id="createCredentialButton">
            <MenuItem eventKey="1" onClick={() => onAddCredential('network')}>
              Network Credential
            </MenuItem>
            <MenuItem eventKey="2" onClick={() => onAddCredential('satellite')}>
              Satellite Credential
            </MenuItem>
            <MenuItem eventKey="2" onClick={() => onAddCredential('vcenter')}>
              VCenter Credential
            </MenuItem>
          </DropdownButton>
        </EmptyState.Action>
        <EmptyState.Action secondary>
          <Button bsStyle="default" onClick={onAddSource}>
            Add Source
          </Button>
        </EmptyState.Action>
      </EmptyState>
    </Row>
  </Grid>
);

CredentialsEmptyState.propTypes = {
  onAddCredential: PropTypes.func,
  onAddSource: PropTypes.func
};

CredentialsEmptyState.defaultProps = {
  onAddCredential: helpers.noop,
  onAddSource: helpers.noop
};

export { CredentialsEmptyState as default, CredentialsEmptyState };
