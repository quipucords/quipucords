import React from 'react';
import cx from 'classnames';
import PropTypes from 'prop-types';
import { ListView, Button, Grid, Icon, Checkbox } from 'patternfly-react';
import { helpers } from '../../common/helpers';
import { SimpleTooltip } from '../simpleTooltIp/simpleTooltip';

class CredentialListItem extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['toggleExpand', 'closeExpand']);
  }

  toggleExpand(expandType) {
    const { item } = this.props;

    if (expandType === item.expandType) {
      item.expanded = !item.expanded;
    } else {
      item.expanded = true;
      item.expandType = expandType;
    }
    this.forceUpdate();
  }

  closeExpand() {
    const { item } = this.props;
    item.expanded = false;
    this.forceUpdate();
  }

  renderActions() {
    const { item, onEdit, onDelete } = this.props;

    return [
      <SimpleTooltip key="editButton" id="editTip" tooltip="Edit Credential">
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
      <SimpleTooltip key="deleteButton" id="deleteTip" tooltip="Delete Credential">
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
    ];
  }

  renderStatusItems() {
    const { item } = this.props;

    let sourceCount = item.sources ? item.sources.length : 0;

    return [
      <ListView.InfoItem
        key="sources"
        className={'list-view-info-item-icon-count ' + (sourceCount === 0 ? 'invisible' : '')}
      >
        <ListView.Expand
          expanded={item.expanded && item.expandType === 'sources'}
          toggleExpanded={() => {
            this.toggleExpand('sources');
          }}
        >
          <strong>{sourceCount}</strong>
          {sourceCount === 1 ? ' Source' : ' Sources'}
        </ListView.Expand>
      </ListView.InfoItem>
    ];
  }

  renderExpansionContents() {
    const { item } = this.props;

    switch (item.expandType) {
      case 'sources':
        item.sources &&
          item.sources.sort((item1, item2) => {
            let cmpVal = item1.source_type.localeCompare(item2.source_type);
            if (cmpVal === 0) {
              cmpVal = item1.name.localeCompare(item2.name);
            }
            return cmpVal;
          });
        return (
          <Grid fluid>
            {item.sources &&
              item.sources.map((source, index) => {
                let typeIcon = helpers.sourceTypeIcon(source.source_type);
                return (
                  <Grid.Row key={index}>
                    <Grid.Col xs={12} sm={4}>
                      <span>
                        <SimpleTooltip id="sourceTypeTip" tooltip={helpers.sourceTypeString(source.source_type)}>
                          <Icon type={typeIcon.type} name={typeIcon.name} />
                        </SimpleTooltip>
                        &nbsp; {source.name}
                      </span>
                    </Grid.Col>
                  </Grid.Row>
                );
              })}
          </Grid>
        );
      default:
        return null;
    }
  }

  render() {
    const { item, selected, onItemSelectChange } = this.props;

    let sourceTypeIcon = helpers.sourceTypeIcon(item.cred_type);

    const classes = cx({
      'quipucords-credential-list-item': true,
      active: selected
    });

    return (
      <ListView.Item
        key={item.id}
        className={classes}
        checkboxInput={<Checkbox checked={selected} bsClass="" onClick={e => onItemSelectChange(item)} />}
        actions={this.renderActions()}
        leftContent={
          <SimpleTooltip id="credentialTypeTip" tooltip={helpers.sourceTypeString(item.cred_type)}>
            <ListView.Icon type={sourceTypeIcon.type} name={sourceTypeIcon.name} />
          </SimpleTooltip>
        }
        heading={item.name}
        description={
          <SimpleTooltip id="methodTip" tooltip="Authorization Type">
            {helpers.authorizationTypeString(item.auth_type)}
          </SimpleTooltip>
        }
        additionalInfo={this.renderStatusItems()}
        compoundExpand
        compoundExpanded={item.expanded}
        onCloseCompoundExpand={this.closeExpand}
      >
        {this.renderExpansionContents()}
      </ListView.Item>
    );
  }
}

CredentialListItem.propTypes = {
  item: PropTypes.object,
  selected: PropTypes.bool,
  onItemSelectChange: PropTypes.func,
  onEdit: PropTypes.func,
  onDelete: PropTypes.func
};

export { CredentialListItem };
