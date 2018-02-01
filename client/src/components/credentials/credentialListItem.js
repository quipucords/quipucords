import React from 'react';
import PropTypes from 'prop-types';
import { ListView, Button, Icon, Checkbox } from 'patternfly-react';
import { SimpleTooltip } from '../simpleTooltIp/simpleTooltip';

class CredentialListItem extends React.Component {
  render() {
    const { item, onItemSelectChange, onEdit, onDelete } = this.props;

    let itemIcon;
    let credentialTypeText;

    switch (item.cred_type) {
      case 'vcenter':
        itemIcon = <ListView.Icon type="pf" name="virtual-machine" />;
        credentialTypeText = 'VCenter';
        break;
      case 'network':
        itemIcon = <ListView.Icon type="pf" name="network" />;
        credentialTypeText = 'Network';
        break;
      case 'satellite':
        itemIcon = <ListView.Icon type="fa" name="space-shuttle" />;
        credentialTypeText = 'Satellite';
        break;
      default:
        itemIcon = null;
        credentialTypeText = '';
    }

    let authType;
    switch (item.auth_type) {
      case 'sshKey':
        authType = 'SSH Key';
        break;
      case 'becomeUser':
        authType = 'Become User';
        break;
      default:
        authType = 'Username & Password';
    }

    return (
      <ListView.Item
        key={item.id}
        checkboxInput={
          <Checkbox
            checked={item.selected}
            bsClass=""
            onClick={e => onItemSelectChange(item)}
          />
        }
        actions={[
          <SimpleTooltip
            key="editButton"
            id="editTip"
            tooltip="Edit Credential"
          >
            <Button
              onClick={() => {
                onEdit(item);
              }}
              bsStyle="link"
              key="editButton"
            >
              <Icon type="pf" name="edit" />
            </Button>
          </SimpleTooltip>,
          <SimpleTooltip
            key="deleteButton"
            id="deleteTip"
            tooltip="Delete Credential"
          >
            <Button
              onClick={() => {
                onDelete(item);
              }}
              bsStyle="link"
              key="removeButton"
            >
              <Icon type="pf" name="delete" />
            </Button>
          </SimpleTooltip>
        ]}
        leftContent={
          <SimpleTooltip id="credentialTypeTip" tooltip={credentialTypeText}>
            {itemIcon}
          </SimpleTooltip>
        }
        heading={item.name}
        description={
          <SimpleTooltip id="methodTip" tooltip="Authorization Type">
            {authType}
          </SimpleTooltip>
        }
        additionalInfo={[
          <ListView.InfoItem
            key="userName"
            className="list-view-info-item-text-count"
          >
            <SimpleTooltip
              id="userTip"
              tooltip={
                item.authType === 'becomeUser' ? 'Become User' : 'Username'
              }
            >
              {item.authType === 'becomeUser'
                ? item.become_user
                : item.username}
            </SimpleTooltip>
          </ListView.InfoItem>,
          <ListView.InfoItem
            key="becomeMethod"
            className="list-view-info-item-text-count"
          >
            <SimpleTooltip id="methodTip" tooltip="Become Method">
              {item.authType === 'becomeUser' ? item.become_method : ''}
            </SimpleTooltip>
          </ListView.InfoItem>
        ]}
      />
    );
  }
}

CredentialListItem.propTypes = {
  item: PropTypes.object,
  onItemSelectChange: PropTypes.func,
  onEdit: PropTypes.func,
  onDelete: PropTypes.func
};

export { CredentialListItem };
